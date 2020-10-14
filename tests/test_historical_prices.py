from trading_ig.rest import IGService
import responses
import json
import pandas as pd
import datetime
import pytest

"""
unit tests for historical prices methods
"""


class TestHistoricalPrices:


    epic_map = {
        'GOLD': 'MT.D.GC.Month2.IP',
        'CORN': 'CO.D.C.Month1.IP',
        'EUROSTX': 'IX.D.STXE.MONTH3.IP',
        'SP500': 'IX.D.SPTRD.MONTH1.IP',
        'AUD': 'CF.D.AUD.DEC.IP', # 'CF.D.AUD.MAR.IP'
    }


    @responses.activate
    def test_historical_prices_v3_defaults_happy(self):

        # fetch_historical_prices v3 - default params

        with open('tests/data/historic_prices.json', 'r') as file:
            response_body = json.loads(file.read())

        responses.add(responses.GET, 'https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP',
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json=response_body,
                      status=200)

        ig_service = IGService('username', 'password', 'api_key', 'DEMO')
        ig_service.crud_session.HEADERS["LOGGED_IN"] = {}
        result = ig_service.fetch_historical_prices_by_epic(epic='MT.D.GC.Month2.IP')
        prices = result['prices']

        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # with no other params, default returns 10 rows at MINUTE resolution
        assert prices.shape[0] == 10
        assert prices.shape[1] == 13

        # assert time series rows are 1 minute apart
        prices['tvalue'] = prices.index
        prices['delta'] = (prices['tvalue'] - prices['tvalue'].shift())
        assert any(prices["delta"].dropna() == datetime.timedelta(minutes=1))


    @responses.activate
    def test_historical_prices_v3_datetime_happy(self):

        # fetch_historical_prices v3 - between two dates, daily resolution

        with open('tests/data/historic_prices_dates.json', 'r') as file:
            response_body = json.loads(file.read())

        responses.add(responses.GET, 'https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP',
                      match_querystring=False,
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json=response_body,
                      status=200)

        ig_service = IGService('username', 'password', 'api_key', 'DEMO')
        ig_service.crud_session.HEADERS["LOGGED_IN"] = {}
        result = ig_service.fetch_historical_prices_by_epic(epic='MT.D.GC.Month2.IP',
                                                            resolution='D',
                                                            start_date='2020-09-01T00:00:00',
                                                            end_date='2020-09-04T23:59:59')

        prices = result['prices']
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 4
        assert prices.shape[1] == 13

        # assert time series rows are 1 day apart
        prices['tvalue'] = prices.index
        prices['delta'] = (prices['tvalue'] - prices['tvalue'].shift())
        assert any(prices["delta"].dropna() == datetime.timedelta(days=1))

        # assert default paging
        assert result['metadata']['pageData']['pageSize'] == 20
        assert result['metadata']['pageData']['pageNumber'] == 1
        assert result['metadata']['pageData']['totalPages'] == 1


    @responses.activate
    def test_historical_prices_v3_num_points_happy(self):

        # fetch_historical_prices v3 - number of data points, weekly resolution

        with open('tests/data/historic_prices_num_points.json', 'r') as file:
            response_body = json.loads(file.read())

        responses.add(responses.GET, 'https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP',
                      match_querystring=False,
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json=response_body,
                      status=200)

        ig_service = IGService('username', 'password', 'api_key', 'DEMO')
        ig_service.crud_session.HEADERS["LOGGED_IN"] = {}
        result = ig_service.fetch_historical_prices_by_epic(epic='MT.D.GC.Month2.IP',
                                                            resolution='W',
                                                            numpoints=10)

        prices = result['prices']
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 10
        assert prices.shape[1] == 13

        # assert time series rows are 1 week apart
        prices['tvalue'] = prices.index
        prices['delta'] = (prices['tvalue'] - prices['tvalue'].shift())
        assert any(prices["delta"].dropna() == datetime.timedelta(weeks=1))


    @responses.activate
    def test_historical_prices_v3_bad_epic(self):

        # fetch_historical_prices v3 - bad epic

        responses.add(responses.GET, 'https://demo-api.ig.com/gateway/deal/prices/MT.D.XX.Month1.IP',
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json={'errorCode': 'error.error.price-history.io-error'},
                      status=404)

        with pytest.raises(Exception):
            ig_service = IGService('username', 'password', 'api_key', 'DEMO')
            ig_service.crud_session.HEADERS["LOGGED_IN"] = {}
            result = ig_service.fetch_historical_prices_by_epic(epic='MT.D.XX.Month1.IP')
            assert result['errorCode'] == 'error.error.price-history.io-error'

    @responses.activate
    def test_historical_prices_v3_bad_date_format(self):

        # fetch_historical_prices v3 - bad date format

        responses.add(responses.GET, 'https://demo-api.ig.com/gateway/deal/prices/MT.D.XX.Month1.IP',
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json={'errorCode': 'Unable to parse datetime=2020/09/01T00:00:00'},
                      status=400)

        '{"errorCode":"Unable to parse datetime=2020/09/01T00:00:00"}'

        with pytest.raises(Exception):
            ig_service = IGService('username', 'password', 'api_key', 'DEMO')
            ig_service.crud_session.HEADERS["LOGGED_IN"] = {}
            result = ig_service.fetch_historical_prices_by_epic(epic='MT.D.GC.Month2.IP',
                                                                        resolution='D',
                                                                        start_date='2020/09/01T00:00:00',
                                                                        end_date='2020-09-04T23:59:59')
            assert result['errorCode'].startswith('Unable to parse datetime')