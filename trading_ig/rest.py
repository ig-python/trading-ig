#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
IG Markets REST API Library for Python
https://labs.ig.com/rest-trading-api-reference
Original version by Lewis Barber - 2014 - https://uk.linkedin.com/in/lewisbarber/
Modified by Femto Trader - 2014-2015 - https://github.com/femtotrader/
"""  # noqa

import json
import logging
import time
from base64 import b64encode, b64decode

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from requests import Session
from urllib.parse import urlparse, parse_qs

from datetime import timedelta, datetime
from .utils import _HAS_PANDAS, _HAS_MUNCH
from .utils import conv_resol, conv_datetime, conv_to_ms, DATE_FORMATS

if _HAS_MUNCH:
    from .utils import munchify

if _HAS_PANDAS:
    from .utils import pd, np
    from pandas import json_normalize

from threading import Thread
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class ApiExceededException(Exception):
    """Raised when our code hits the IG endpoint too often"""
    pass


class IGException(Exception):
    pass


class IGSessionCRUD(object):
    """Session with CRUD operation"""

    BASE_URL = None

    def __init__(self, base_url, api_key, session):
        self.BASE_URL = base_url
        self.API_KEY = api_key
        self.session = session

        self.session.headers.update({
            "X-IG-API-KEY": self.API_KEY,
            'Content-Type': 'application/json',
            'Accept': 'application/json; charset=UTF-8'
        })

    def _get_session(self, session):
        """Returns a Requests session if session is None
        or session if it's not None (cached session
        with requests-cache for example)

        :param session:
        :return:
        """
        if session is None:
            session = self.session  # requests Session
        else:
            session = session
        return session

    def _url(self, endpoint):
        """Returns url from endpoint and base url"""
        return self.BASE_URL + endpoint

    def create(self, endpoint, params, session, version):
        """Create = POST"""
        url = self._url(endpoint)
        session = self._get_session(session)
        session.headers.update({'VERSION': version})
        response = session.post(url, data=json.dumps(params))
        logging.info(f"POST '{endpoint}', resp {response.status_code}")
        if response.status_code in [401, 403]:
            if 'exceeded-api-key-allowance' in response.text:
                raise ApiExceededException()
            else:
                raise IGException(f"HTTP error: {response.status_code} {response.text}")

        return response

    def read(self, endpoint, params, session, version):
        """Read = GET"""
        url = self._url(endpoint)
        session = self._get_session(session)
        session.headers.update({'VERSION': version})
        response = session.get(url, params=params)
        # handle 'read_session' with 'fetchSessionTokens=true'
        handle_session_tokens(response, self.session)
        logging.info(f"GET '{endpoint}', resp {response.status_code}")
        return response

    def update(self, endpoint, params, session, version):
        """Update = PUT"""
        url = self._url(endpoint)
        session = self._get_session(session)
        session.headers.update({'VERSION': version})
        response = session.put(url, data=json.dumps(params))
        logging.info(f"PUT '{endpoint}', resp {response.status_code}")
        return response

    def delete(self, endpoint, params, session, version):
        """Delete = POST"""
        url = self._url(endpoint)
        session = self._get_session(session)
        session.headers.update({'VERSION': version})
        session.headers.update({'_method': 'DELETE'})
        response = session.post(url, data=json.dumps(params))
        logging.info(f"DELETE (POST) '{endpoint}', resp {response.status_code}")
        if '_method' in session.headers:
            del session.headers['_method']
        return response

    def req(self, action, endpoint, params, session, version):
        """Send a request (CREATE READ UPDATE or DELETE)"""
        d_actions = {
            "create": self.create,
            "read": self.read,
            "update": self.update,
            "delete": self.delete,
        }
        return d_actions[action](endpoint, params, session, version)


class IGService:

    D_BASE_URL = {
        "live": "https://api.ig.com/gateway/deal",
        "demo": "https://demo-api.ig.com/gateway/deal",
    }

    API_KEY = None
    IG_USERNAME = None
    IG_PASSWORD = None
    _refresh_token = None
    _valid_until = None

    def __init__(
        self,
        username,
        password,
        api_key,
        acc_type="demo",
        acc_number=None,
        session=None,
        return_dataframe=_HAS_PANDAS,
        return_munch=_HAS_MUNCH,
        retryer=None,
        use_rate_limiter=False
    ):
        """Constructor, calls the method required to connect to
        the API (accepts acc_type = LIVE or DEMO)"""
        self.API_KEY = api_key
        self.IG_USERNAME = username
        self.IG_PASSWORD = password
        self.ACC_NUMBER = acc_number
        self._retryer = retryer
        self._use_rate_limiter = use_rate_limiter
        self._bucket_threads_run = False
        try:
            self.BASE_URL = self.D_BASE_URL[acc_type.lower()]
        except Exception:
            raise IGException("Invalid account type '%s', please provide LIVE or DEMO" %
                              acc_type)

        self.return_dataframe = return_dataframe
        self.return_munch = return_munch

        if session is None:
            self.session = Session()  # Requests Session (global)
        else:
            self.session = session

        self.crud_session = IGSessionCRUD(self.BASE_URL, self.API_KEY, self.session)

    def setup_rate_limiter(self, ):

        data = self.get_client_apps()
        for acc in data:
            if acc['apiKey'] == self.API_KEY:
                break

        # If self.create_session() is called a second time, we should exit any currently running threads
        self._exit_bucket_threads()

        # Horrific magic number to reduce API published allowable requests per minute to a
        # value that wont result in 403 -> error.public-api.exceeded-account-trading-allowance
        # Tested for non_trading = 30 (live) and 10 (demo) requests per minute.
        # This wouldn't be needed if IG's API functioned as published!
        MAGIC_NUMBER = 2

        self._trading_requests_per_minute = acc['allowanceAccountTrading'] - MAGIC_NUMBER
        logging.info(f"Published IG Trading Request limits for trading request: "
                     f"{acc['allowanceAccountTrading']} per minute. Using: {self._trading_requests_per_minute}")

        self._non_trading_requests_per_minute = acc['allowanceAccountOverall'] - MAGIC_NUMBER
        logging.info(f"Published IG Trading Request limits for non-trading request: "
                     f"{acc['allowanceAccountOverall']} per minute. Using {self._non_trading_requests_per_minute}")

        time.sleep(60.0 / self._non_trading_requests_per_minute)

        self._bucket_threads_run = True  # Thread exit variable

        # Create a leaky token bucket for trading requests
        trading_requests_burst = 1  # If IG ever allow bursting, increase this
        self._trading_requests_queue = Queue(trading_requests_burst)
        # prefill the bucket so we can burst
        [self._trading_requests_queue.put(True) for i in range(trading_requests_burst)]
        token_bucket_trading_thread = Thread(target=self._token_bucket_trading,)
        token_bucket_trading_thread.start()
        self._trading_times = []

        # Create a leaky token bucket for non-trading requests
        non_trading_requests_burst = 1  # If IG ever allow bursting, increase this
        self._non_trading_requests_queue = Queue(non_trading_requests_burst)
        # prefill the bucket so we can burst
        [self._non_trading_requests_queue.put(True) for i in range(non_trading_requests_burst)]
        token_bucket_non_trading_thread = Thread(target=self._token_bucket_non_trading,)
        token_bucket_non_trading_thread.start()
        self._non_trading_times = []

        # TODO
        # Create a leaky token bucket for allowanceAccountHistoricalData
        return

    def _token_bucket_trading(self, ):
        while self._bucket_threads_run:
            time.sleep(60.0/self._trading_requests_per_minute)
            self._trading_requests_queue.put(True, block=True)
        return

    def _token_bucket_non_trading(self, ):
        while self._bucket_threads_run:
            time.sleep(60.0/self._non_trading_requests_per_minute)
            self._non_trading_requests_queue.put(True, block=True)
        return

    def trading_rate_limit_pause_or_pass(self, ):
        if self._use_rate_limiter:
            self._trading_requests_queue.get(block=True)
            self._trading_times.append(time.time())
            self._trading_times = [req_time for req_time in self._trading_times if req_time > time.time()-60]
            logging.info(f'Number of trading requests in last 60 seonds = '
                         f'{len(self._trading_times)} of {self._trading_requests_per_minute}')
        return

    def non_trading_rate_limit_pause_or_pass(self, ):
        if self._use_rate_limiter:
            self._non_trading_requests_queue.get(block=True)
            self._non_trading_times.append(time.time())
            self._non_trading_times = [req_time for req_time in self._non_trading_times if req_time > time.time()-60]
            logging.info(f'Number of non trading requests in last 60 seonds = '
                         f'{len(self._non_trading_times)} of {self._non_trading_requests_per_minute}')
        return

    def _exit_bucket_threads(self,):
        if self._use_rate_limiter:
            if self._bucket_threads_run:
                self._bucket_threads_run = False
                try:
                    self._trading_requests_queue.get(block=False)
                except Empty:
                    pass
                try:
                    self._non_trading_requests_queue.get(block=False)
                except Empty:
                    pass
        return

    def _get_session(self, session):
        """Returns a Requests session (from self.session) if session is None
        or session if it's not None (cached session with requests-cache
        for example)
        """
        if session is None:
            session = self.session  # requests Session
        else:
            assert isinstance(
                session, Session
            ), "session must be <requests.session.Session object> not %s" % type(
                session
            )
            session = session
        return session

    def _req(self, action, endpoint, params, session, version='1', check=True):
        """
        Wraps the _request() function, applying a tenacity.Retrying object if configured
        """
        if self._retryer is not None:
            result = self._retryer.__call__(self._request, action, endpoint, params, session, version, check)
        else:
            result = self._request(action, endpoint, params, session, version, check)

        return result

    def _request(self, action, endpoint, params, session, version='1', check=True):
        """Creates a CRUD request and returns response"""
        session = self._get_session(session)
        if check:
            self._check_session()
        response = self.crud_session.req(action, endpoint, params, session, version)

        if response.status_code >= 500:
            raise (IGException(f"Server problem: status code: {response.status_code}, reason: {response.reason}"))

        response.encoding = 'utf-8'
        if self._api_limit_hit(response.text):
            raise ApiExceededException()
        return response

    @staticmethod
    def _api_limit_hit(response_text):
        # note we don't check for historical data allowance - it only gets reset once a week
        return 'exceeded-api-key-allowance' in response_text or \
               'exceeded-account-allowance' in response_text or \
               'exceeded-account-trading-allowance' in response_text

    # ---------- PARSE_RESPONSE ----------- #

    @staticmethod
    def parse_response(*args, **kwargs):
        """Parses JSON response
        returns dict
        exception raised when error occurs"""
        response = json.loads(*args, **kwargs)
        if "errorCode" in response:
            raise (Exception(response["errorCode"]))
        return response

    # --------- END -------- #

    # ------ DATAFRAME TOOLS -------- #

    @staticmethod
    def colname_unique(d_cols):
        """Returns a set of column names (unique)"""
        s = set()
        for _, lst in d_cols.items():
            for colname in lst:
                s.add(colname)
        return s

    @staticmethod
    def expand_columns(data, d_cols, flag_col_prefix=False, col_overlap_allowed=None):
        """Expand columns"""
        if col_overlap_allowed is None:
            col_overlap_allowed = []
        for (col_lev1, lst_col) in d_cols.items():
            ser = data[col_lev1]
            del data[col_lev1]
            for col in lst_col:
                if col not in data.columns or col in col_overlap_allowed:
                    if flag_col_prefix:
                        colname = col_lev1 + "_" + col
                    else:
                        colname = col
                    data[colname] = ser.map(lambda x: x[col], na_action='ignore')
                else:
                    raise (NotImplementedError("col overlap: %r" % col))
        return data

    # -------- END ------- #

    # -------- ACCOUNT ------- #

    def fetch_accounts(self, session=None):
        """Returns a list of accounts belonging to the logged-in client"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        endpoint = "/accounts"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            data = pd.DataFrame(data["accounts"])
            d_cols = {"balance": [u"available", u"balance", u"deposit", u"profitLoss"]}
            data = self.expand_columns(data, d_cols, False)

            if len(data) == 0:
                columns = [
                    "accountAlias",
                    "accountId",
                    "accountName",
                    "accountType",
                    "balance",
                    "available",
                    "balance",
                    "deposit",
                    "profitLoss",
                    "canTransferFrom",
                    "canTransferTo",
                    "currency",
                    "preferred",
                    "status",
                ]
                data = pd.DataFrame(columns=columns)
                return data

        return data

    def fetch_account_preferences(self, session=None):
        """
        Gets the preferences for the logged in account
        :param session: session object. Optional
        :type session: requests.Session
        :return: preference values
        :rtype: dict
        """
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        endpoint = "/accounts/preferences"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        prefs = self.parse_response(response.text)
        return prefs

    def update_account_preferences(self, trailing_stops_enabled=False, session=None):
        """
        Updates the account preferences. Currently only one value supported - trailing stops
        :param trailing_stops_enabled: whether trailing stops should be enabled for the account
        :type trailing_stops_enabled: bool
        :param session: session object. Optional
        :type session: requests.Session
        :return: status of the update request
        :rtype: str
        """
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        endpoint = "/accounts/preferences"
        action = "update"
        params['trailingStopsEnabled'] = 'true' if trailing_stops_enabled else 'false'
        response = self._req(action, endpoint, params, session, version)
        update_status = self.parse_response(response.text)
        return update_status['status']

    def fetch_account_activity_by_period(self, milliseconds, session=None):
        """
        Returns the account activity history for the last specified period
        """
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        milliseconds = conv_to_ms(milliseconds)
        params = {}
        url_params = {"milliseconds": milliseconds}
        endpoint = "/history/activity/{milliseconds}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            data = pd.DataFrame(data["activities"])

            if len(data) == 0:
                columns = [
                    "actionStatus", "activity", "activityHistoryId", "channel", "currency", "date",
                    "dealId", "epic", "level", "limit", "marketName", "period", "result", "size",
                    "stop", "stopType", "time"
                ]
                data = pd.DataFrame(columns=columns)
                return data

        return data

    def fetch_account_activity_by_date(self, from_date: datetime, to_date: datetime, session=None):
        """
        Returns the account activity history for period between the specified dates
        """
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        if from_date is None or to_date is None:
            raise IGException("Both from_date and to_date must be specified")
        if from_date > to_date:
            raise IGException("from_date must be before to_date")

        params = {}
        url_params = {
            "fromDate": from_date.strftime('%d-%m-%Y'),
            "toDate": to_date.strftime('%d-%m-%Y')
        }
        endpoint = "/history/activity/{fromDate}/{toDate}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if _HAS_PANDAS and self.return_dataframe:

            data = pd.DataFrame(data["activities"])

            if len(data) == 0:
                columns = [
                    "actionStatus", "activity", "activityHistoryId", "channel", "currency", "date",
                    "dealId", "epic", "level", "limit", "marketName", "period", "result", "size",
                    "stop", "stopType", "time"
                ]
                data = pd.DataFrame(columns=columns)
                return data

        return data

    def fetch_account_activity_v2(
            self,
            from_date: datetime = None,
            to_date: datetime = None,
            max_span_seconds: int = None,
            page_size: int = 20,
            session=None):

        """
        Returns the account activity history (v2)

        If the result set spans multiple 'pages', this method will automatically get all the results and
        bundle them into one object.

        :param from_date: start date and time. Optional
        :type from_date: datetime
        :param to_date: end date and time. A date without time refers to the end of that day. Defaults to
        today. Optional
        :type to_date: datetime
        :param max_span_seconds: Limits the timespan in seconds through to current time (not applicable if a
        date range has been specified). Default 600. Optional
        :type max_span_seconds: int
        :param page_size: number of records per page. Default 20. Optional. Use 0 to turn off paging
        :type page_size: int
        :param session: session object. Optional
        :type session: Session
        :return: results set
        :rtype: Pandas DataFrame if configured, otherwise a dict
        """
        self.non_trading_rate_limit_pause_or_pass()
        version = "2"
        params = {}
        if from_date:
            params["from"] = from_date.strftime('%Y-%m-%dT%H:%M:%S')
        if to_date:
            params["to"] = to_date.strftime('%Y-%m-%dT%H:%M:%S')
        if max_span_seconds:
            params["maxSpanSeconds"] = max_span_seconds
        params["pageSize"] = page_size
        endpoint = "/history/activity/"
        action = "read"
        data = {}
        activities = []
        pagenumber = 1
        more_results = True

        while more_results:
            params["pageNumber"] = pagenumber
            response = self._req(action, endpoint, params, session, version)
            data = self.parse_response(response.text)
            activities.extend(data["activities"])
            page_data = data["metadata"]["pageData"]
            if page_data["totalPages"] == 0 or \
                    (page_data["pageNumber"] == page_data["totalPages"]):
                more_results = False
            else:
                pagenumber += 1

        data["activities"] = activities
        if _HAS_PANDAS and self.return_dataframe:
            data = pd.DataFrame(data["activities"])

        return data

    def fetch_account_activity(
            self,
            from_date: datetime = None,
            to_date: datetime = None,
            detailed=False,
            deal_id: str = None,
            fiql_filter: str = None,
            page_size: int = 50,
            session=None):

        """
        Returns the account activity history (v3)

        If the result set spans multiple 'pages', this method will automatically get all the results and
        bundle them into one object.

        :param from_date: start date and time. Optional
        :type from_date: datetime
        :param to_date: end date and time. A date without time refers to the end of that day. Defaults to
        today. Optional
        :type to_date: datetime
        :param detailed: Indicates whether to retrieve additional details about the activity. Default False. Optional
        :type detailed: bool
        :param deal_id: deal ID. Optional
        :type deal_id: str
        :param fiql_filter: FIQL filter (supported operators: ==|!=|,|;). Optional
        :type fiql_filter: str
        :param page_size: page size (min: 10, max: 500). Default 50. Optional
        :type page_size: int
        :param session: session object. Optional
        :type session: Session
        :return: results set
        :rtype: Pandas DataFrame if configured, otherwise a dict
        """
        self.non_trading_rate_limit_pause_or_pass()
        version = "3"
        params = {}
        if from_date:
            params["from"] = from_date.strftime('%Y-%m-%dT%H:%M:%S')
        if to_date:
            params["to"] = to_date.strftime('%Y-%m-%dT%H:%M:%S')
        if detailed:
            params["detailed"] = "true"
        if deal_id:
            params["dealId"] = deal_id
        if fiql_filter:
            params["filter"] = fiql_filter

        params["pageSize"] = page_size
        endpoint = "/history/activity/"
        action = "read"
        data = {}
        activities = []
        more_results = True

        while more_results:
            response = self._req(action, endpoint, params, session, version)
            data = self.parse_response(response.text)
            activities.extend(data["activities"])
            paging = data["metadata"]["paging"]
            if paging["next"] is None:
                more_results = False
            else:
                parse_result = urlparse(paging["next"])
                query = parse_qs(parse_result.query)
                logging.debug(f"fetch_account_activity() next query: '{query}'")
                if 'from' in query:
                    params["from"] = query["from"][0]
                else:
                    del params["from"]
                if 'to' in query:
                    params["to"] = query["to"][0]
                else:
                    del params["to"]

        data["activities"] = activities
        if _HAS_PANDAS and self.return_dataframe:
            if detailed:
                data = self.format_activities(data)
            else:
                data = pd.DataFrame(data["activities"])

        return data

    @staticmethod
    def format_activities(data):
        data = pd.json_normalize(data["activities"],
                                 record_path=['details', ['actions']],
                                 meta=['date', 'epic', 'period', 'dealId', 'channel', 'type', 'status', 'description',
                                       ['details', 'marketName'],
                                       ['details', 'goodTillDate'],
                                       ['details', 'currency'],
                                       ['details', 'direction'],
                                       ['details', 'level'],
                                       ['details', 'stopLevel'],
                                       ['details', 'stopDistance'],
                                       ['details', 'guaranteedStop'],
                                       ['details', 'trailingStopDistance'],
                                       ['details', 'trailingStep'],
                                       ['details', 'limitLevel'],
                                       ['details', 'limitDistance']],
                                 )

        data = data.rename(columns={'details.marketName': 'marketName',
                                    'details.goodTillDate': 'goodTillDate',
                                    'details.currency': 'currency',
                                    'details.direction': 'direction',
                                    'details.level': 'level',
                                    'details.stopLevel': 'stopLevel',
                                    'details.stopDistance': 'stopDistance',
                                    'details.guaranteedStop': 'guaranteedStop',
                                    'details.trailingStopDistance': 'trailingStopDistance',
                                    'details.trailingStep': 'trailingStep',
                                    'details.limitLevel': 'limitLevel',
                                    'details.limitDistance': 'limitDistance'})

        cols = data.columns.tolist()
        cols = cols[2:] + cols[:2]
        data = data[cols]

        return data

    def fetch_transaction_history_by_type_and_period(
        self, milliseconds, trans_type, session=None
    ):
        """Returns the transaction history for the specified transaction
        type and period"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        milliseconds = conv_to_ms(milliseconds)
        params = {}
        url_params = {"milliseconds": milliseconds, "trans_type": trans_type}
        endpoint = "/history/transactions/{trans_type}/{milliseconds}".format(
            **url_params
        )
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            data = pd.DataFrame(data["transactions"])

            if len(data) == 0:
                columns = [
                    "cashTransaction",
                    "closeLevel",
                    "currency",
                    "date",
                    "instrumentName",
                    "openLevel",
                    "period",
                    "profitAndLoss",
                    "reference",
                    "size",
                    "transactionType",
                ]
                data = pd.DataFrame(columns=columns)
                return data

        return data

    def fetch_transaction_history(
        self,
        trans_type=None,
        from_date=None,
        to_date=None,
        max_span_seconds=None,
        page_size=None,
        page_number=None,
        session=None,
    ):
        """Returns the transaction history for the specified transaction
        type and period"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "2"
        params = {}
        if trans_type:
            params["type"] = trans_type
        if from_date:
            if hasattr(from_date, "isoformat"):
                from_date = from_date.isoformat()
            params["from"] = from_date
        if to_date:
            if hasattr(to_date, "isoformat"):
                to_date = to_date.isoformat()
            params["to"] = to_date
        if max_span_seconds:
            params["maxSpanSeconds"] = max_span_seconds
        if page_size:
            params["pageSize"] = page_size
        if page_number:
            params["pageNumber"] = page_number

        endpoint = "/history/transactions"
        action = "read"

        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            data = pd.DataFrame(data["transactions"])

            if len(data) == 0:
                columns = [
                    "cashTransaction",
                    "closeLevel",
                    "currency",
                    "date",
                    "dateUtc",
                    "instrumentName",
                    "openLevel",
                    "period",
                    "profitAndLoss",
                    "reference",
                    "size",
                    "transactionType",
                ]
                data = pd.DataFrame(columns=columns)
                return data

        return data

    # -------- END -------- #

    # -------- DEALING -------- #

    def fetch_deal_by_deal_reference(self, deal_reference, session=None):
        """Returns a deal confirmation for the given deal reference"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        url_params = {"deal_reference": deal_reference}
        endpoint = "/confirms/{deal_reference}".format(**url_params)
        action = "read"
        for i in range(5):
            response = self._req(action, endpoint, params, session, version)
            if not response.status_code == 200:
                logger.info("Deal reference %s not found, retrying." % deal_reference)
                time.sleep(1)
            else:
                break
        data = self.parse_response(response.text)
        return data

    def fetch_open_position_by_deal_id(self, deal_id, session=None):
        """Return the open position by deal id for the active account"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "2"
        params = {}
        url_params = {"deal_id": deal_id}
        endpoint = "/positions/{deal_id}".format(**url_params)
        action = "read"
        for i in range(5):
            response = self._req(action, endpoint, params, session, version)
            if not response.status_code == 200:
                logger.info("Deal id %s not found, retrying." % deal_id)
                time.sleep(1)
            else:
                break
        data = self.parse_response(response.text)
        return data

    def fetch_open_positions(self, session=None, version='2'):
        """
        Returns all open positions for the active account. Supports both v1 and v2
        :param session: session object, otional
        :type session: Session
        :param version: API version, 1 or 2
        :type version: str
        :return: table of position data, one per row
        :rtype: pd.Dataframe
        """
        self.non_trading_rate_limit_pause_or_pass()
        params = {}
        endpoint = "/positions"
        action = "read"
        for i in range(5):
            response = self._req(action, endpoint, params, session, version)
            if not response.status_code == 200:
                logger.info("Error fetching open positions, retrying.")
                time.sleep(1)
            else:
                break
        data = self.parse_response(response.text)

        if self.return_dataframe:

            list = data["positions"]
            data = pd.DataFrame(list)

            cols = {
                "position": [
                    "contractSize", "createdDate", "createdDateUTC", "dealId", "dealReference", "size", "direction",
                    "limitLevel", "level", "currency", "controlledRisk", "stopLevel", "trailingStep",
                    "trailingStopDistance", "limitedRiskPremium"
                ],
                "market": [
                    "instrumentName", "expiry", "epic", "instrumentType", "lotSize", "high", "low",
                    "percentageChange", "netChange", "bid", "offer", "updateTime", "updateTimeUTC",
                    "delayTime", "streamingPricesAvailable", "marketStatus", "scalingFactor"
                ]
            }

            if version == '1':
                cols['position'].remove('createdDateUTC')
                cols['position'].remove('dealReference')
                cols['position'].remove('size')
                cols['position'].insert(3, 'dealSize')
                cols['position'].remove('level')
                cols['position'].insert(6, 'openLevel')
                cols['market'].remove('updateTimeUTC')

            if len(data) == 0:
                data = pd.DataFrame(columns=self.colname_unique(cols))
                return data

            data = self.expand_columns(data, cols)

        return data

    def close_open_position(
        self,
        deal_id,
        direction,
        epic,
        expiry,
        level,
        order_type,
        quote_id,
        size,
        session=None,
    ):
        """Closes one or more OTC positions"""
        self.trading_rate_limit_pause_or_pass()
        version = "1"
        params = {
            "dealId": deal_id,
            "direction": direction,
            "epic": epic,
            "expiry": expiry,
            "level": level,
            "orderType": order_type,
            "quoteId": quote_id,
            "size": size,
        }
        endpoint = "/positions/otc"
        action = "delete"
        response = self._req(action, endpoint, params, session, version)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise IGException(response.text)

    def create_open_position(
        self,
        currency_code,
        direction,
        epic,
        expiry,
        force_open,
        guaranteed_stop,
        level,
        limit_distance,
        limit_level,
        order_type,
        quote_id,
        size,
        stop_distance,
        stop_level,
        trailing_stop,
        trailing_stop_increment,
        session=None,
    ):
        """Creates an OTC position"""
        self.trading_rate_limit_pause_or_pass()
        version = "2"
        params = {
            "currencyCode": currency_code,
            "direction": direction,
            "epic": epic,
            "expiry": expiry,
            "forceOpen": force_open,
            "guaranteedStop": guaranteed_stop,
            "level": level,
            "limitDistance": limit_distance,
            "limitLevel": limit_level,
            "orderType": order_type,
            "quoteId": quote_id,
            "size": size,
            "stopDistance": stop_distance,
            "stopLevel": stop_level,
            "trailingStop": trailing_stop,
            "trailingStopIncrement": trailing_stop_increment,
        }

        endpoint = "/positions/otc"
        action = "create"

        response = self._req(action, endpoint, params, session, version)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise IGException(response.text)

    def update_open_position(
            self,
            limit_level,
            stop_level,
            deal_id,
            guaranteed_stop=False,
            trailing_stop=False,
            trailing_stop_distance=None,
            trailing_stop_increment=None,
            session=None,
            version='2'):
        """Updates an OTC position"""
        self.trading_rate_limit_pause_or_pass()
        params = {}
        if limit_level is not None:
            params["limitLevel"] = limit_level
        if stop_level is not None:
            params["stopLevel"] = stop_level
        if guaranteed_stop:
            params["guaranteedStop"] = 'true'
        if trailing_stop:
            params["trailingStop"] = 'true'
        if trailing_stop_distance is not None:
            params["trailingStopDistance"] = trailing_stop_distance
        if trailing_stop_increment is not None:
            params["trailingStopIncrement"] = trailing_stop_increment

        url_params = {"deal_id": deal_id}
        endpoint = "/positions/otc/{deal_id}".format(**url_params)
        action = "update"
        response = self._req(action, endpoint, params, session, version)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise IGException(response.text)

    def fetch_working_orders(self, session=None, version='2'):
        """Returns all open working orders for the active account"""
        self.non_trading_rate_limit_pause_or_pass()  # ?? maybe considered trading request
        params = {}
        endpoint = "/workingorders"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            lst = data["workingOrders"]
            data = pd.DataFrame(lst)

            col_names_v1 = [u"size", u"trailingStopDistance", u"direction", u"level", u"requestType", u"currencyCode",
                            u"contingentLimit", u"trailingTriggerIncrement", u"dealId", u"contingentStop", u"goodTill",
                            u"controlledRisk", u"trailingStopIncrement", u"createdDate", u"epic",
                            u"trailingTriggerDistance", u"dma"]
            col_names_v2 = [u"createdDate", u"currencyCode", u"dealId", u"direction", u"dma", u"epic",
                            u"goodTillDate", u"goodTillDateISO", u"guaranteedStop", u"limitDistance",
                            u"orderLevel", u"orderSize", u"orderType", u"stopDistance", u"timeInForce"]

            d_cols = {
                "marketData": [
                    u"instrumentName",
                    u"exchangeId",
                    u"streamingPricesAvailable",
                    u"offer",
                    u"low",
                    u"bid",
                    u"updateTime",
                    u"expiry",
                    u"high",
                    u"marketStatus",
                    u"delayTime",
                    u"lotSize",
                    u"percentageChange",
                    u"epic",
                    u"netChange",
                    u"instrumentType",
                    u"scalingFactor",
                ]
            }

            if version == '1':
                d_cols["workingOrderData"] = col_names_v1
            else:
                d_cols["workingOrderData"] = col_names_v2

            if len(data) == 0:
                data = pd.DataFrame(columns=self.colname_unique(d_cols))
                return data

            col_overlap_allowed = ["epic"]

            data = self.expand_columns(data, d_cols, False, col_overlap_allowed)

            # d = data.to_dict()
            # data = pd.concat(list(map(pd.DataFrame, d.values())),
            #                  keys=list(d.keys())).T

        return data

    def create_working_order(
        self,
        currency_code,
        direction,
        epic,
        expiry,
        guaranteed_stop,
        level,
        size,
        time_in_force,
        order_type,
        limit_distance=None,
        limit_level=None,
        stop_distance=None,
        stop_level=None,
        good_till_date=None,
        deal_reference=None,
        force_open=False,
        session=None,
    ):
        """Creates an OTC working order"""
        self.trading_rate_limit_pause_or_pass()
        version = "2"
        if good_till_date is not None and type(good_till_date) is not int:
            good_till_date = conv_datetime(good_till_date, version)

        params = {
            "currencyCode": currency_code,
            "direction": direction,
            "epic": epic,
            "expiry": expiry,
            "guaranteedStop": guaranteed_stop,
            "level": level,
            "size": size,
            "timeInForce": time_in_force,
            "type": order_type,
        }
        if limit_distance:
            params["limitDistance"] = limit_distance
        if limit_level:
            params["limitLevel"] = limit_level
        if stop_distance:
            params["stopDistance"] = stop_distance
        if stop_level:
            params["stopLevel"] = stop_level
        if deal_reference:
            params["dealReference"] = deal_reference
        if force_open:
            params["forceOpen"] = 'true'
        if good_till_date:
            params["goodTillDate"] = good_till_date

        endpoint = "/workingorders/otc"
        action = "create"

        response = self._req(action, endpoint, params, session, version)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise IGException(response.text)

    def delete_working_order(self, deal_id, session=None):
        """Deletes an OTC working order"""
        self.trading_rate_limit_pause_or_pass()
        version = "2"
        params = {}
        url_params = {"deal_id": deal_id}
        endpoint = "/workingorders/otc/{deal_id}".format(**url_params)
        action = "delete"
        response = self._req(action, endpoint, params, session, version)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise IGException(response.text)

    def update_working_order(
        self,
        good_till_date,
        level,
        limit_distance,
        limit_level,
        stop_distance,
        stop_level,
        guaranteed_stop,
        time_in_force,
        order_type,
        deal_id,
        session=None,
    ):
        """Updates an OTC working order"""
        self.trading_rate_limit_pause_or_pass()
        version = "2"
        if good_till_date is not None and type(good_till_date) is not int:
            good_till_date = conv_datetime(good_till_date, version)
        params = {
            "goodTillDate": good_till_date,
            "limitDistance": limit_distance,
            "level": level,
            "limitLevel": limit_level,
            "stopDistance": stop_distance,
            "stopLevel": stop_level,
            "guaranteedStop": guaranteed_stop,
            "timeInForce": time_in_force,
            "type": order_type,
        }
        url_params = {"deal_id": deal_id}
        endpoint = "/workingorders/otc/{deal_id}".format(**url_params)
        action = "update"
        response = self._req(action, endpoint, params, session, version)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)["dealReference"]
            return self.fetch_deal_by_deal_reference(deal_reference)
        else:
            raise IGException(response.text)

    # -------- END -------- #

    # -------- MARKETS -------- #

    def fetch_client_sentiment_by_instrument(self, market_id, session=None):
        """Returns the client sentiment for the given instrument's market"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        if isinstance(market_id, (list,)):
            market_ids = ",".join(market_id)
            url_params = {"market_ids": market_ids}
            endpoint = "/clientsentiment/?marketIds={market_ids}".format(**url_params)
        else:
            url_params = {"market_id": market_id}
            endpoint = "/clientsentiment/{market_id}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_munch:
            data = munchify(data)
        return data

    def fetch_related_client_sentiment_by_instrument(self, market_id, session=None):
        """Returns a list of related (also traded) client sentiment for
        the given instrument's market"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        url_params = {"market_id": market_id}
        endpoint = "/clientsentiment/related/{market_id}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data["clientSentiments"])
        return data

    def fetch_top_level_navigation_nodes(self, session=None):
        """Returns all top-level nodes (market categories) in the market
        navigation hierarchy."""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        endpoint = "/marketnavigation"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            data["markets"] = pd.DataFrame(data["markets"])
            if len(data["markets"]) == 0:
                columns = [
                    "bid",
                    "delayTime",
                    "epic",
                    "expiry",
                    "high",
                    "instrumentName",
                    "instrumentType",
                    "lotSize",
                    "low",
                    "marketStatus",
                    "netChange",
                    "offer",
                    "otcTradeable",
                    "percentageChange",
                    "scalingFactor",
                    "streamingPricesAvailable",
                    "updateTime",
                ]
                data["markets"] = pd.DataFrame(columns=columns)
            data["nodes"] = pd.DataFrame(data["nodes"])
            if len(data["nodes"]) == 0:
                columns = ["id", "name"]
                data["nodes"] = pd.DataFrame(columns=columns)
        # if self.return_munch:
        #     # ToFix: ValueError: The truth value of a DataFrame is ambiguous.
        #     # Use a.empty, a.bool(), a.item(), a.any() or a.all().
        #     from .utils import munchify
        #     data = munchify(data)
        return data

    def fetch_sub_nodes_by_node(self, node, session=None):
        """Returns all sub-nodes of the given node in the market
        navigation hierarchy"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        url_params = {"node": node}
        endpoint = "/marketnavigation/{node}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:

            data["markets"] = pd.DataFrame(data["markets"])
            data["nodes"] = pd.DataFrame(data["nodes"])
        return data

    def fetch_market_by_epic(self, epic, session=None):
        """Returns the details of the given market"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "3"
        params = {}
        url_params = {"epic": epic}
        endpoint = "/markets/{epic}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_munch:
            data = munchify(data)
        return data

    def fetch_markets_by_epics(self, epics, detailed=True, session=None, version='2'):
        """
        Returns the details of the given markets
        :param epics: comma separated list of epics
        :type epics: str
        :param detailed: Whether to return detailed info or snapshot data only. Only supported for
        version 2. Optional, default True
        :type detailed: bool
        :param session: session object. Optional, default None
        :type session: requests.Session
        :param version: IG API method version. Optional, default '2'
        :type version: str
        :return: list of market details
        :rtype: Munch instance if configured, else dict
        """
        self.non_trading_rate_limit_pause_or_pass()
        params = {"epics": epics}
        if version == '2':
            params["filter"] = 'ALL' if detailed else 'SNAPSHOT_ONLY'
        endpoint = "/markets"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_munch:
            data = munchify(data['marketDetails'])
        else:
            data = data['marketDetails']
        return data

    def search_markets(self, search_term, session=None):
        """Returns all markets matching the search term"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        endpoint = "/markets"
        params = {"searchTerm": search_term}
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data["markets"])
        return data

    def format_prices(self, prices, version, flag_calc_spread=False):
        """Format prices data as a DataFrame with hierarchical columns"""

        if len(prices) == 0:
            raise (Exception("Historical price data not found"))

        def cols(typ):
            return {
                "openPrice.%s" % typ: "Open",
                "highPrice.%s" % typ: "High",
                "lowPrice.%s" % typ: "Low",
                "closePrice.%s" % typ: "Close",
                "lastTradedVolume": "Volume",
            }

        last = prices[0]["lastTradedVolume"] or prices[0]["closePrice"]["lastTraded"]
        df = json_normalize(prices)
        df = df.set_index("snapshotTime")
        df.index = pd.to_datetime(df.index, format=DATE_FORMATS[int(version)])
        df.index.name = "DateTime"

        df_ask = df[
            ["openPrice.ask", "highPrice.ask", "lowPrice.ask", "closePrice.ask"]
        ]
        df_ask = df_ask.rename(columns=cols("ask"))

        df_bid = df[
            ["openPrice.bid", "highPrice.bid", "lowPrice.bid", "closePrice.bid"]
        ]
        df_bid = df_bid.rename(columns=cols("bid"))

        if flag_calc_spread:
            df_spread = df_ask - df_bid

        if last:
            df_last = df[
                [
                    "openPrice.lastTraded",
                    "highPrice.lastTraded",
                    "lowPrice.lastTraded",
                    "closePrice.lastTraded",
                    "lastTradedVolume",
                ]
            ]
            df_last = df_last.rename(columns=cols("lastTraded"))

        data = [df_bid, df_ask]
        keys = ["bid", "ask"]
        if flag_calc_spread:
            data.append(df_spread)
            keys.append("spread")

        if last:
            data.append(df_last)
            keys.append("last")

        df2 = pd.concat(data, axis=1, keys=keys)
        return df2

    def flat_prices(self, prices, version):

        """Format price data as a flat DataFrame, no hierarchy"""

        if len(prices) == 0:
            raise (Exception("Historical price data not found"))

        df = json_normalize(prices)
        df = df.set_index("snapshotTimeUTC")
        df.index = pd.to_datetime(df.index, format="%Y-%m-%dT%H:%M:%S")
        df.index.name = "DateTime"
        df = df.drop(columns=['snapshotTime',
                              'openPrice.lastTraded',
                              'closePrice.lastTraded',
                              'highPrice.lastTraded',
                              'lowPrice.lastTraded'])
        df = df.rename(columns={"openPrice.bid": "open.bid",
                                "openPrice.ask": "open.ask",
                                "closePrice.bid": "close.bid",
                                "closePrice.ask": "close.ask",
                                "highPrice.bid": "high.bid",
                                "highPrice.ask": "high.ask",
                                "lowPrice.bid": "low.bid",
                                "lowPrice.ask": "low.ask",
                                "lastTradedVolume": "volume"})
        return df

    def mid_prices(self, prices, version):

        """Format price data as a flat DataFrame, no hierarchy, calculating mid prices"""

        if len(prices) == 0:
            raise (Exception("Historical price data not found"))

        df = json_normalize(prices)
        df = df.set_index("snapshotTimeUTC")
        df.index = pd.to_datetime(df.index, format="%Y-%m-%dT%H:%M:%S")
        df.index.name = "DateTime"

        df['Open'] = df[['openPrice.bid', 'openPrice.ask']].mean(axis=1)
        df['High'] = df[['highPrice.bid', 'highPrice.ask']].mean(axis=1)
        df['Low'] = df[['lowPrice.bid', 'lowPrice.ask']].mean(axis=1)
        df['Close'] = df[['closePrice.bid', 'closePrice.ask']].mean(axis=1)

        df = df.drop(columns=['snapshotTime', 'openPrice.lastTraded', 'closePrice.lastTraded',
                              'highPrice.lastTraded', 'lowPrice.lastTraded',
                              "openPrice.bid", "openPrice.ask",
                              "closePrice.bid", "closePrice.ask",
                              "highPrice.bid", "highPrice.ask",
                              "lowPrice.bid", "lowPrice.ask"])
        df = df.rename(columns={"lastTradedVolume": "Volume"})

        return df

    def fetch_historical_prices_by_epic(
        self,
        epic,
        resolution=None,
        start_date=None,
        end_date=None,
        numpoints=None,
        pagesize=20,
        session=None,
        format=None,
        wait=1
    ):

        """
        Fetches historical prices for the given epic.

        This method wraps the IG v3 /prices/{epic} endpoint. With this method you can
        choose to get either a fixed number of prices in the past, or to get the
        prices between two points in time. By default it will return the last 10
        prices at 1 minute resolution.

        If the result set spans multiple 'pages', this method will automatically
        get all the results and bundle them into one object.

        :param epic: (str) The epic key for which historical prices are being
            requested
        :param resolution: (str, optional) timescale resolution. Expected values
            are 1Min, 2Min, 3Min, 5Min, 10Min, 15Min, 30Min, 1H, 2H, 3H, 4H, D,
            W, M. Default is 1Min
        :param start_date: (datetime, optional) date range start, format
            yyyy-MM-dd'T'HH:mm:ss
        :param end_date: (datetime, optional) date range end, format
            yyyy-MM-dd'T'HH:mm:ss
        :param numpoints: (int, optional) number of data points. Default is 10
        :param pagesize: (int, optional) number of data points. Default is 20
        :param session: (Session, optional) session object
        :param format: (function, optional) function to convert the raw
            JSON response
        :param wait: (int, optional) how many seconds to wait between successive
            calls in a multi-page scenario. Default is 1
        :returns: Pandas DataFrame if configured, otherwise a dict
        :raises Exception: raises an exception if any error is encountered
        """

        version = "3"
        params = {}
        if resolution and self.return_dataframe:
            params["resolution"] = conv_resol(resolution)
        if start_date:
            params["from"] = start_date
        if end_date:
            params["to"] = end_date
        if numpoints:
            params["max"] = numpoints
        params["pageSize"] = pagesize
        url_params = {"epic": epic}
        endpoint = "/prices/{epic}".format(**url_params)
        action = "read"
        prices = []
        pagenumber = 1
        more_results = True

        while more_results:
            params["pageNumber"] = pagenumber
            response = self._req(action, endpoint, params, session, version)
            data = self.parse_response(response.text)
            prices.extend(data["prices"])
            page_data = data["metadata"]["pageData"]
            if page_data["totalPages"] == 0 or \
                    (page_data["pageNumber"] == page_data["totalPages"]):
                more_results = False
            else:
                pagenumber += 1
            time.sleep(wait)

        data["prices"] = prices

        if format is None:
            format = self.format_prices
        if self.return_dataframe:
            data["prices"] = format(data["prices"], version)
            data['prices'] = data['prices'].fillna(value=np.nan)
        self.log_allowance(data["metadata"])
        return data

    def fetch_historical_prices_by_epic_and_num_points(self, epic, resolution,
                                                       numpoints, session=None,
                                                       format=None):
        """Returns a list of historical prices for the given epic, resolution,
        number of points"""
        version = "2"
        if self.return_dataframe:
            resolution = conv_resol(resolution)
        params = {}
        url_params = {"epic": epic, "resolution": resolution, "numpoints": numpoints}
        endpoint = "/prices/{epic}/{resolution}/{numpoints}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if format is None:
            format = self.format_prices
        if self.return_dataframe:
            data["prices"] = format(data["prices"], version)
            data['prices'] = data['prices'].fillna(value=np.nan)
        return data

    def fetch_historical_prices_by_epic_and_date_range(
        self, epic, resolution, start_date, end_date, session=None, format=None, version='2'
    ):
        """
        Returns a list of historical prices for the given epic, resolution, multiplier and date range. Supports
        both versions 1 and 2
        :param epic: IG epic
        :type epic: str
        :param resolution: timescale for returned data. Expected values 'M', 'D', '1H' etc
        :type resolution: str
        :param start_date: start date for returned data. For v1, format '2020:09:01-00:00:00', for v2 use
            '2020-09-01 00:00:00'
        :type start_date: str
        :param end_date: end date for returned data. For v1, format '2020:09:01-00:00:00', for v2 use
            '2020-09-01 00:00:00'
        :type end_date: str
        :param session: HTTP session
        :type session: requests.Session
        :param format: function defining how the historic price data should be converted into a Dataframe
        :type format: function
        :param version: API method version
        :type version: str
        :return: historic data
        :rtype: dict, with 'prices' element as pandas.Dataframe
        """
        if self.return_dataframe:
            resolution = conv_resol(resolution)
        params = {}
        if version == '1':
            start_date = conv_datetime(start_date, version)
            end_date = conv_datetime(end_date, version)
            params = {"startdate": start_date, "enddate": end_date}
            url_params = {"epic": epic, "resolution": resolution}
            endpoint = "/prices/{epic}/{resolution}".format(**url_params)
        else:
            url_params = {"epic": epic, "resolution": resolution, "startDate": start_date, "endDate": end_date}
            endpoint = "/prices/{epic}/{resolution}/{startDate}/{endDate}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        del self.session.headers["VERSION"]
        data = self.parse_response(response.text)
        if format is None:
            format = self.format_prices
        if self.return_dataframe:
            data["prices"] = format(data["prices"], version)
            data['prices'] = data['prices'].fillna(value=np.nan)
        return data

    def log_allowance(self, data):
        remaining_allowance = data['allowance']['remainingAllowance']
        allowance_expiry_secs = data['allowance']['allowanceExpiry']
        allowance_expiry = datetime.today() + timedelta(seconds=allowance_expiry_secs)
        logger.info("Historic price data allowance: %s remaining until %s" %
                    (remaining_allowance, allowance_expiry))

    # -------- END -------- #

    # -------- WATCHLISTS -------- #

    def fetch_all_watchlists(self, session=None):
        """Returns all watchlists belonging to the active account"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        endpoint = "/watchlists"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data["watchlists"])
        return data

    def create_watchlist(self, name, epics, session=None):
        """Creates a watchlist"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {"name": name, "epics": epics}
        endpoint = "/watchlists"
        action = "create"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    def delete_watchlist(self, watchlist_id, session=None):
        """Deletes a watchlist"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        url_params = {"watchlist_id": watchlist_id}
        endpoint = "/watchlists/{watchlist_id}".format(**url_params)
        action = "delete"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    def fetch_watchlist_markets(self, watchlist_id, session=None):
        """Returns the given watchlist's markets"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        url_params = {"watchlist_id": watchlist_id}
        endpoint = "/watchlists/{watchlist_id}".format(**url_params)
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data["markets"])
        return data

    def add_market_to_watchlist(self, watchlist_id, epic, session=None):
        """Adds a market to a watchlist"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {"epic": epic}
        url_params = {"watchlist_id": watchlist_id}
        endpoint = "/watchlists/{watchlist_id}".format(**url_params)
        action = "update"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    def remove_market_from_watchlist(self, watchlist_id, epic, session=None):
        """Remove a market from a watchlist"""
        self.non_trading_rate_limit_pause_or_pass()
        version = "1"
        params = {}
        url_params = {"watchlist_id": watchlist_id, "epic": epic}
        endpoint = "/watchlists/{watchlist_id}/{epic}".format(**url_params)
        action = "delete"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    # -------- END -------- #

    # -------- LOGIN -------- #

    def logout(self, session=None):
        """Log out of the current session"""
        version = "1"
        params = {}
        endpoint = "/session"
        action = "delete"
        self._req(action, endpoint, params, session, version)
        self.session.close()
        self._exit_bucket_threads()

    def get_encryption_key(self, session=None):
        """Get encryption key to encrypt the password"""
        endpoint = "/session/encryptionKey"
        session = self._get_session(session)
        response = session.get(self.BASE_URL + endpoint)
        if not response.ok:
            raise IGException("Could not get encryption key for login.")
        data = response.json()
        return data["encryptionKey"], data["timeStamp"]

    def encrypted_password(self, session=None):
        """Encrypt password for login"""
        key, timestamp = self.get_encryption_key(session)
        rsakey = RSA.importKey(b64decode(key))
        string = self.IG_PASSWORD + "|" + str(int(timestamp))
        message = b64encode(string.encode())
        return b64encode(PKCS1_v1_5.new(rsakey).encrypt(message)).decode()

    def create_session(self, session=None, encryption=False, version='2'):
        """
        Creates a session, obtaining tokens for subsequent API access

        ** April 2021 v3 has been implemented, but is not the default for now

        :param session: HTTP session
        :type session: requests.Session
        :param encryption: whether or not the password should be encrypted. Required for some regions
        :type encryption: Boolean
        :param version: API method version
        :type version: str
        :return: JSON response body, parsed into dict
        :rtype: dict
        """
        if version == '3' and self.ACC_NUMBER is None:
            raise IGException('Account number must be set for v3 sessions')

        logging.info(f"Creating new v{version} session for user '{self.IG_USERNAME}' at '{self.BASE_URL}'")
        password = self.encrypted_password(session) if encryption else self.IG_PASSWORD
        params = {"identifier": self.IG_USERNAME, "password": password}
        if encryption:
            params["encryptedPassword"] = True
        endpoint = "/session"
        action = "create"
        response = self._req(action, endpoint, params, session, version, check=False)
        self._manage_headers(response)
        data = self.parse_response(response.text)

        if self._use_rate_limiter:
            self.setup_rate_limiter()

        return data

    def refresh_session(self, session=None, version='1'):
        """
        Refreshes a v3 session. Tokens only last for 60 seconds, so need to be renewed regularly
        :param session: HTTP session object
        :type session: requests.Session
        :param version: API method version
        :type version: str
        :return: HTTP status code
        :rtype: int
        """
        logging.info(f"Refreshing session '{self.IG_USERNAME}'")
        params = {"refresh_token": self._refresh_token}
        endpoint = "/session/refresh-token"
        action = "create"
        response = self._req(action, endpoint, params, session, version, check=False)
        self._handle_oauth(json.loads(response.text))
        return response.status_code

    def _manage_headers(self, response):
        """
        Manages authentication headers - different behaviour depending on the session creation version
        :param response: HTTP response
        :type response: requests.Response
        """
        # handle v1 and v2 logins
        handle_session_tokens(response, self.session)
        # handle v3 logins
        if response.text:
            self.session.headers.update({'IG-ACCOUNT-ID': self.ACC_NUMBER})
            payload = json.loads(response.text)
            if 'oauthToken' in payload:
                self._handle_oauth(payload['oauthToken'])

    def _handle_oauth(self, oauth):
        """
        Handle the v3 headers during session creation and refresh
        :param oauth: 'oauth' portion of the response body
        :type oauth: dict
        """
        access_token = oauth['access_token']
        token_type = oauth['token_type']
        self.session.headers.update({'Authorization': f"{token_type} {access_token}"})
        self._refresh_token = oauth['refresh_token']
        validity = int(oauth['expires_in'])
        self._valid_until = datetime.now() + timedelta(seconds=validity)

    def _check_session(self):
        """
        Check the v3 session status before making an API request:
            - v3 tokens only last for 60 seconds
            - if possible, the session can be renewed with a special refresh token
            - if not, a new session will be created
        """
        logging.debug("Checking session status...")
        if self._valid_until is not None and datetime.now() > self._valid_until:
            if self._refresh_token:
                # we are in a v3 session, need to refresh
                try:
                    logging.info("Current session has expired, refreshing...")
                    self.refresh_session()
                except IGException:
                    logging.info("Refresh failed, logging in again...")
                    self._refresh_token = None
                    self._valid_until = None
                    del self.session.headers['Authorization']
                    self.create_session(version='3')

    def switch_account(self, account_id, default_account, session=None):
        """Switches active accounts, optionally setting the default account"""
        version = "1"
        params = {"accountId": account_id, "defaultAccount": default_account}
        endpoint = "/session"
        action = "update"
        response = self._req(action, endpoint, params, session, version)
        self._manage_headers(response)
        data = self.parse_response(response.text)
        return data

    def read_session(self, fetch_session_tokens='false', session=None):
        """Retrieves current session details"""
        version = "1"
        params = {"fetchSessionTokens": fetch_session_tokens}
        endpoint = "/session"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        if not response.ok:
            raise IGException("Error in read_session() %s" % response.status_code)
        data = self.parse_response(response.text)
        return data

    # -------- END -------- #

    # -------- GENERAL -------- #

    def get_client_apps(self, session=None):
        """Returns a list of client-owned applications"""
        version = "1"
        params = {}
        endpoint = "/operations/application"
        action = "read"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    def update_client_app(
        self,
        allowance_account_overall,
        allowance_account_trading,
        api_key,
        status,
        session=None,
    ):
        """Updates an application"""
        version = "1"
        params = {
            "allowanceAccountOverall": allowance_account_overall,
            "allowanceAccountTrading": allowance_account_trading,
            "apiKey": api_key,
            "status": status,
        }
        endpoint = "/operations/application"
        action = "update"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    def disable_client_app_key(self, session=None):
        """
        Disables the current application key from processing further requests.
        Disabled keys may be re-enabled via the My Account section on
        the IG Web Dealing Platform.
        """
        version = "1"
        params = {}
        endpoint = "/operations/application/disable"
        action = "update"
        response = self._req(action, endpoint, params, session, version)
        data = self.parse_response(response.text)
        return data

    # -------- END -------- #


def handle_session_tokens(response, session):
    """
    Copy session tokens from response to headers, so they will be present for all future requests
    :param response: HTTP response object
    :type response: requests.Response
    :param session: HTTP session object
    :type session: requests.Session
    """
    if "CST" in response.headers:
        session.headers.update({'CST': response.headers['CST']})
    if "X-SECURITY-TOKEN" in response.headers:
        session.headers.update({'X-SECURITY-TOKEN': response.headers['X-SECURITY-TOKEN']})
