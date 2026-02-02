from trading_ig.rest import (
    IGService,
    IGException,
    ApiExceededException,
    TokenInvalidException,
)
from trading_ig.config import config
import pandas as pd
from datetime import datetime, timedelta
import pytest
from random import randint, choice
import logging
import time
from tenacity import (
    Retrying,
    wait_exponential,
    retry_if_exception_type,
    stop_after_attempt,
)

try:
    import munch  # noqa: F401

    munch_installed = True
except ImportError:
    munch_installed = False

RETRYABLE = (ApiExceededException, TokenInvalidException)


@pytest.fixture(scope="module")
def retrying():
    """test fixture creates a tenacity.Retrying instance"""
    return Retrying(
        wait=wait_exponential(),
        retry=retry_if_exception_type(RETRYABLE),
    )


@pytest.fixture(scope="module")
def limited_retrying():
    """test fixture creates a tenacity.Retrying instance with max 3 attempts"""
    return Retrying(
        wait=wait_exponential(),
        retry=retry_if_exception_type(RETRYABLE),
        stop=stop_after_attempt(3),
    )


@pytest.fixture(autouse=True)
def logging_setup():
    """sets logging for each test"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@pytest.fixture(scope="module", params=["2", "3"], ids=["v2 session", "v3 session"])
def ig_service(request, retrying):
    """
    test fixture logs into IG with the configured credentials.
    Tests both v2 and v3 types
    """
    if config.acc_type == "LIVE":
        pytest.fail("this integration test should not be executed with a LIVE account")
    ig_service = IGService(
        config.username,
        config.password,
        config.api_key,
        config.acc_type,
        acc_number=config.acc_number,
        retryer=retrying,
    )
    service = ig_service.create_session(version=request.param)
    if request.param == "2" and service["accountType"] != "SPREADBET":
        pytest.fail("Integration test currently only works with a spreadbet account")

    yield ig_service
    ig_service.logout()


# TODO refactor for new navigation API
@pytest.fixture()
def top_level_nodes(ig_service: IGService):
    """test fixture gets the top level navigation nodes"""
    response = ig_service.fetch_top_level_navigation_nodes()
    return response["nodes"]


@pytest.fixture()
def watchlists(ig_service: IGService):
    """test fixture gets all watchlists"""
    return ig_service.fetch_all_watchlists()


@pytest.fixture()
def watchlist_id(ig_service: IGService):
    """test fixture creates a dummy watchlist for use in tests,
    and returns the ID. In teardown it also deletes the dummy watchlist"""
    epics = ["CS.D.GBPUSD.TODAY.IP", "IX.D.FTSE.DAILY.IP"]
    now = datetime.now()
    data = ig_service.create_watchlist(f"test_{now.strftime('%Y%m%d%H%H%S')}", epics)
    watchlist_id = data["watchlistId"]
    yield watchlist_id
    ig_service.delete_watchlist(watchlist_id)


class TestIntegration:
    def test_create_session_no_encryption(self, retrying):
        ig_service = IGService(
            config.username,
            config.password,
            config.api_key,
            config.acc_type,
            retryer=retrying,
        )
        ig_service.create_session()
        assert "CST" in ig_service.session.headers

    def test_create_session_encrypted_password(self, retrying):
        ig_service = IGService(
            config.username,
            config.password,
            config.api_key,
            config.acc_type,
            retryer=retrying,
        )
        ig_service.create_session(encryption=True)
        assert "CST" in ig_service.session.headers

    def test_fetch_accounts(self, ig_service: IGService):
        response = ig_service.fetch_accounts()
        preferred = response.loc[response["preferred"]]
        assert all(preferred["balance"] > 0)

    def test_accounts_prefs(self, ig_service: IGService):
        # turn off trailing stops
        update_status = ig_service.update_account_preferences(
            trailing_stops_enabled=False
        )
        assert update_status == "SUCCESS"

        # check trailing stops are turned off
        enabled_status = ig_service.fetch_account_preferences()["trailingStopsEnabled"]
        assert enabled_status is False
        time.sleep(5)

        # turn on trailing stops
        update_status = ig_service.update_account_preferences(
            trailing_stops_enabled=True
        )
        assert update_status == "SUCCESS"
        time.sleep(5)

        # check trailing stops are turned on
        enabled_status = ig_service.fetch_account_preferences()["trailingStopsEnabled"]
        assert enabled_status is True

    def test_fetch_account_activity_by_period(self, ig_service: IGService):
        response = ig_service.fetch_account_activity_by_period(10000)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_account_activity_by_date(self, ig_service: IGService):
        to_date = datetime.now()
        from_date = to_date - timedelta(days=7)
        response = ig_service.fetch_account_activity_by_date(from_date, to_date)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_account_activity_v2_span(self, ig_service: IGService):
        period = 7 * 24 * 60 * 60  # 7 days
        response = ig_service.fetch_account_activity_v2(max_span_seconds=period)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_account_activity_v2_dates(self, ig_service):
        to_date = datetime(2021, 7, 31)
        from_date = to_date - timedelta(days=7)
        response = ig_service.fetch_account_activity_v2(
            from_date=from_date, to_date=to_date
        )
        assert isinstance(response, pd.DataFrame)

    def test_fetch_account_activity_from(self, ig_service: IGService):
        to_date = datetime.now() - timedelta(days=3)
        from_date = to_date - timedelta(days=7)
        response = ig_service.fetch_account_activity(from_date=from_date)
        assert isinstance(response, pd.DataFrame)
        assert response.shape[1] == 9

    def test_fetch_account_activity_from_to(self, ig_service: IGService):
        to_date = datetime(2023, 7, 18)
        from_date = to_date - timedelta(days=7)
        response = ig_service.fetch_account_activity(
            from_date=from_date, to_date=to_date
        )
        assert isinstance(response, pd.DataFrame)
        assert response.shape[1] == 9

    def test_fetch_account_activity_detailed(self, ig_service):
        to_date = datetime(2023, 7, 18)
        from_date = to_date - timedelta(days=7)
        response = ig_service.fetch_account_activity(
            from_date=from_date, to_date=to_date, detailed=True
        )
        assert isinstance(response, pd.DataFrame)
        assert response.shape[1] == 23

    def test_fetch_account_activity_old(self, ig_service: IGService):
        from_date = datetime(1970, 1, 1)
        to_date = from_date + timedelta(days=7)
        response = ig_service.fetch_account_activity(
            from_date=from_date, to_date=to_date
        )
        assert isinstance(response, pd.DataFrame)
        assert response.shape[0] == 0

    def test_fetch_account_activity_fiql(self, ig_service: IGService):
        to_date = datetime(2023, 7, 18)
        from_date = to_date - timedelta(days=30)
        response = ig_service.fetch_account_activity(
            from_date=from_date, to_date=to_date, fiql_filter="channel==PUBLIC_WEB_API"
        )
        assert isinstance(response, pd.DataFrame)
        assert response.shape[1] == 9

    def test_init_bad_account_type(self, retrying):
        with pytest.raises(IGException):
            IGService(
                config.username,
                config.password,
                config.api_key,
                "wrong",
                retryer=retrying,
            )

    def test_fetch_transaction_history_by_type_and_period(self, ig_service: IGService):
        response = ig_service.fetch_transaction_history_by_type_and_period(10000, "ALL")
        assert isinstance(response, pd.DataFrame)

    def test_create_session_bad_password(self, retrying):
        ig_service = IGService(
            config.username, "wrong", config.api_key, config.acc_type, retryer=retrying
        )
        with pytest.raises(IGException):
            ig_service.create_session()

    def test_fetch_open_positions(self, ig_service):
        response = ig_service.fetch_open_positions()
        assert isinstance(response, pd.DataFrame)

    def test_fetch_open_positions_v1(self, ig_service: IGService):
        response = ig_service.fetch_open_positions(version="1")
        assert isinstance(response, pd.DataFrame)

    def test_create_session_bad_username(self, retrying):
        ig_service = IGService(
            "wrong", config.password, config.api_key, config.acc_type, retryer=retrying
        )
        with pytest.raises(IGException):
            ig_service.create_session()

    def test_fetch_working_orders(self, ig_service: IGService):
        response = ig_service.fetch_working_orders()
        assert isinstance(response, pd.DataFrame)

    def test_create_session_bad_api_key(self, retrying):
        ig_service = IGService(
            config.username, config.password, "wrong", config.acc_type, retryer=retrying
        )
        with pytest.raises(IGException):
            ig_service.create_session()

    @pytest.mark.xfail(reason="Navigation API has been changed by IG")
    def test_fetch_top_level_navigation_nodes(self, top_level_nodes):
        assert isinstance(top_level_nodes, pd.DataFrame)

    def test_create_session_v3_no_acc_num(self, retrying):
        ig_service = IGService(
            config.username,
            config.password,
            config.api_key,
            config.acc_type,
            retryer=retrying,
        )
        with pytest.raises(IGException):
            ig_service.create_session(version="3")

    def test_create_session_v3(self, retrying):
        ig_service = IGService(
            config.username,
            config.password,
            config.api_key,
            config.acc_type,
            acc_number=config.acc_number,
            retryer=retrying,
        )
        ig_service.create_session(version="3")
        assert "X-IG-API-KEY" in ig_service.session.headers
        assert "Authorization" in ig_service.session.headers
        assert "IG-ACCOUNT-ID" in ig_service.session.headers
        assert len(ig_service.fetch_accounts()) == 2

    @pytest.mark.slow  # will be skipped unless run with 'pytest --runslow'
    def test_session_v3_refresh(self, retrying):
        """
        Tests refresh capability of v3 sessions. It makes repeated calls to the
        'fetch_accounts' endpoint, with random sleep times in between, to show/test the
        different scenarios. Will take a long time to run
        """
        ig_service = IGService(
            config.username,
            config.password,
            config.api_key,
            config.acc_type,
            acc_number=config.acc_number,
            retryer=retrying,
        )
        ig_service.create_session(version="3")
        delay_choice = [(1, 59), (60, 650)]
        for count in range(1, 20):
            data = ig_service.fetch_accounts()
            logging.info(f"Account count: {len(data)}")
            option = choice(delay_choice)
            wait = randint(option[0], option[1])
            logging.info(f"Waiting for {wait} seconds...")
            time.sleep(wait)

    def test_read_session(self, ig_service: IGService):
        ig_service.read_session()
        assert "X-IG-API-KEY" in ig_service.session.headers

        if ig_service.session.headers["VERSION"] == "2":
            assert "CST" in ig_service.session.headers
            assert "X-SECURITY-TOKEN" in ig_service.session.headers
            assert "Authorization" not in ig_service.session.headers
            assert "IG-ACCOUNT-ID" not in ig_service.session.headers

        if ig_service.session.headers["VERSION"] == "3":
            assert "CST" not in ig_service.session.headers
            assert "X-SECURITY-TOKEN" not in ig_service.session.headers
            assert "Authorization" in ig_service.session.headers
            assert "IG-ACCOUNT-ID" in ig_service.session.headers

    def test_read_session_fetch_session_tokens(self, ig_service: IGService):
        ig_service.read_session(fetch_session_tokens="true")
        assert "X-IG-API-KEY" in ig_service.session.headers
        assert "CST" in ig_service.session.headers
        assert "X-SECURITY-TOKEN" in ig_service.session.headers

        if ig_service.session.headers["VERSION"] == "2":
            assert "Authorization" not in ig_service.session.headers
            assert "IG-ACCOUNT-ID" not in ig_service.session.headers

        if ig_service.session.headers["VERSION"] == "3":
            assert "Authorization" in ig_service.session.headers
            assert "IG-ACCOUNT-ID" in ig_service.session.headers

    @staticmethod
    def get_random_market_id():
        market_ids = [
            "US500",
            "FT100",
            "USTECH",
            "GC",
            "CL",
            "W",
            "GBPUSD",
            "USDJPY",
            "EURCHF",
            "10YRTND",
            "FGBL",
            "FLG",
            "BITCOIN",
            "ETHUSD",
            "LTCUSD",
            "BP-UK",
            "VOD-UK",
            "TSLA-US",
        ]
        rand_index = randint(0, len(market_ids) - 1)
        market_id = market_ids[rand_index]
        return market_id

    def test_fetch_client_sentiment_by_instrument(self, ig_service: IGService):
        market_id = self.get_random_market_id()
        response = ig_service.fetch_client_sentiment_by_instrument(market_id)
        self.assert_sentiment(response)

    def test_fetch_client_sentiment_by_instrument_multiple(self, ig_service: IGService):
        market_id_list = []
        for i in range(1, 5):
            market_id_list.append(self.get_random_market_id())
        response = ig_service.fetch_client_sentiment_by_instrument(market_id_list)
        for sentiment in response["clientSentiments"]:
            self.assert_sentiment(sentiment)

    @staticmethod
    def assert_sentiment(response):
        long = response["longPositionPercentage"]
        short = response["shortPositionPercentage"]
        assert isinstance(response, dict)
        assert isinstance(long, float)
        assert isinstance(short, float)
        assert long + short == 100.0

    @pytest.mark.xfail(reason="Navigation API has been changed by IG")
    def test_fetch_sub_nodes_by_node(self, ig_service: IGService, top_level_nodes):
        rand_index = randint(0, len(top_level_nodes) - 1)
        response = ig_service.fetch_sub_nodes_by_node(rand_index)
        assert isinstance(response["markets"], pd.DataFrame)
        assert isinstance(response["nodes"], pd.DataFrame)

    def test_fetch_all_watchlists(self, watchlists):
        assert isinstance(watchlists, pd.DataFrame)
        default = watchlists[watchlists["defaultSystemWatchlist"]]
        assert any(default["id"] == "Popular Markets")

    def test_fetch_watchlist_markets(self, ig_service: IGService, watchlists):
        rand_index = randint(0, len(watchlists) - 1)
        watchlist_id = watchlists.iloc[rand_index]["id"]
        response = ig_service.fetch_watchlist_markets(watchlist_id)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_market_by_epic(self, ig_service: IGService):
        response = ig_service.fetch_market_by_epic("CS.D.EURUSD.MINI.IP")
        assert isinstance(response, dict)

    @pytest.mark.skipif(not munch_installed, reason="Requires munch")
    def test_fetch_markets_by_epics(self, ig_service: IGService):
        markets_list = ig_service.fetch_markets_by_epics(
            "IX.D.SPTRD.MONTH1.IP,IX.D.FTSE.DAILY.IP", version="1"
        )
        assert isinstance(markets_list, list)
        assert len(markets_list) == 2
        assert markets_list[0].instrument.name == "FTSE 100"
        assert markets_list[0].dealingRules is not None
        assert markets_list[1].instrument.name == "US 500"

        markets_list = ig_service.fetch_markets_by_epics(
            "MT.D.PL.Month2.IP,MT.D.PA.Month1.IP,MT.D.HG.Month1.IP", detailed=False
        )
        assert len(markets_list) == 3
        assert markets_list[0].instrument.name is None
        assert markets_list[0].snapshot.bid != 0
        assert markets_list[0].snapshot.offer != 0
        assert markets_list[0].dealingRules is None

        assert markets_list[1].instrument.name is None
        assert markets_list[1].snapshot.bid != 0
        assert markets_list[1].snapshot.offer != 0
        assert markets_list[1].dealingRules is None

        assert markets_list[2].instrument.name is None
        assert markets_list[2].snapshot.bid != 0
        assert markets_list[2].snapshot.offer != 0
        assert markets_list[2].dealingRules is None

    def test_search_markets(self, ig_service: IGService):
        search_term = "EURUSD"
        response = ig_service.search_markets(search_term)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_historical_prices_by_epic_and_numpoints(self, ig_service: IGService):
        response = ig_service.fetch_historical_prices_by_epic_and_num_points(
            "CS.D.EURUSD.MINI.IP", "h", 4
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert len(response["prices"]) == 4

    def test_fetch_historical_prices_by_epic_and_numpoints_flat(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_num_points(
            "CS.D.EURUSD.MINI.IP", "h", 4, format=ig_service.flat_prices
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert response["prices"].shape[0] == 4
        assert response["prices"].shape[1] == 9

    def test_fetch_historical_prices_by_epic_and_numpoints_mid(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_num_points(
            "CS.D.EURUSD.MINI.IP", "h", 4, format=ig_service.mid_prices
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert response["prices"].shape[0] == 4
        assert response["prices"].shape[1] == 5

    def test_fetch_historical_prices_by_epic_and_date_range_v1(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP",
            "D",
            "2020:09:01-00:00:00",
            "2020:09:04-23:59:59",
            version="1",
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert len(response["prices"]) == 4

    def test_fetch_historical_prices_by_epic_and_date_range(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP", "D", "2020-09-01 00:00:00", "2020-09-04 23:59:59"
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert len(response["prices"]) == 4

    def test_fetch_historical_prices_by_epic_and_date_range_flat_v1(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP",
            "D",
            "2020-09-01 00:00:00",
            "2020-09-04 23:59:59",
            format=ig_service.flat_prices,
            version="1",
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert response["prices"].shape[0] == 4
        assert response["prices"].shape[1] == 9

    def test_fetch_historical_prices_by_epic_and_date_range_flat_v2(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP",
            "D",
            "2020-09-01 00:00:00",
            "2020-09-04 23:59:59",
            format=ig_service.flat_prices,
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert response["prices"].shape[0] == 4
        assert response["prices"].shape[1] == 9

    def test_fetch_historical_prices_by_epic_and_date_range_mid_v1(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP",
            "D",
            "2020-09-01 00:00:00",
            "2020-09-04 23:59:59",
            format=ig_service.mid_prices,
            version="1",
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert response["prices"].shape[0] == 4
        assert response["prices"].shape[1] == 5

    def test_fetch_historical_prices_by_epic_and_date_range_mid_v2(
        self, ig_service: IGService
    ):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP",
            "D",
            "2020-09-01 00:00:00",
            "2020-09-04 23:59:59",
            format=ig_service.mid_prices,
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert response["prices"].shape[0] == 4
        assert response["prices"].shape[1] == 5

    def test_fetch_historical_prices_by_epic_dates(self, ig_service: IGService):
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP",
            resolution="D",
            start_date="2020-09-01T00:00:00",
            end_date="2020-09-04T23:59:59",
        )

        prices = result["prices"]
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)
        assert prices.shape[0] == 4
        assert prices.shape[1] == 13

        # assert time series rows are 1 day apart
        prices["tvalue"] = prices.index
        prices["delta"] = prices["tvalue"] - prices["tvalue"].shift()
        assert any(prices["delta"].dropna() == timedelta(days=1))

        # assert default paging
        assert result["metadata"]["pageData"]["pageSize"] == 20
        assert result["metadata"]["pageData"]["pageNumber"] == 1
        assert result["metadata"]["pageData"]["totalPages"] == 1

    def test_fetch_historical_prices_by_epic_numpoints(self, ig_service: IGService):
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP", resolution="W", numpoints=10
        )

        prices = result["prices"]
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 10
        assert prices.shape[1] == 13

        # assert time series rows are 1 week apart
        prices["tvalue"] = prices.index
        prices["delta"] = prices["tvalue"] - prices["tvalue"].shift()
        assert any(prices["delta"].dropna() == timedelta(weeks=1))

    def test_fetch_historical_prices_by_epic_numpoints_default_paged(
        self, ig_service: IGService
    ):
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP", resolution="W", numpoints=21
        )

        # assert default paged row count
        assert result["prices"].shape[0] == 21
        assert result["metadata"]["pageData"]["pageNumber"] == 2

    def test_fetch_historical_prices_by_epic_numpoints_custom_paged(
        self, ig_service: IGService
    ):
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP", resolution="W", numpoints=6, pagesize=2
        )

        # assert default paged row count
        assert result["prices"].shape[0] == 6
        assert result["metadata"]["pageData"]["pageNumber"] == 3

    def test_fetch_historical_prices_by_epic_flat(self, ig_service: IGService):
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP",
            resolution="W",
            numpoints=5,
            format=ig_service.flat_prices,
        )

        prices = result["prices"]
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 5
        assert prices.shape[1] == 9

    def test_fetch_historical_prices_by_epic_mid(self, ig_service: IGService):
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP",
            resolution="W",
            numpoints=5,
            format=ig_service.mid_prices,
        )

        prices = result["prices"]
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 5
        assert prices.shape[1] == 5

    @pytest.mark.skipif(not munch_installed, reason="Requires munch")
    def test_create_open_position(self, ig_service: IGService):
        epic = "IX.D.FTSE.DAILY.IP"
        market_info = ig_service.fetch_market_by_epic(epic)
        status = market_info.snapshot.marketStatus
        min_bet = market_info.dealingRules.minDealSize.value
        bid = market_info.snapshot.bid
        offer = market_info.snapshot.offer
        if status != "TRADEABLE":
            pytest.skip("Skipping open position test, market not open")

        open_result = ig_service.create_open_position(
            epic=epic,
            direction="BUY",
            currency_code="GBP",
            order_type="MARKET",
            expiry="DFB",
            force_open="false",
            guaranteed_stop="false",
            size=min_bet,
            level=None,
            limit_level=None,
            limit_distance=None,
            quote_id=None,
            stop_distance=None,
            stop_level=None,
            trailing_stop=None,
            trailing_stop_increment=None,
        )
        assert open_result["dealStatus"] == "ACCEPTED"
        assert open_result["reason"] == "SUCCESS"
        time.sleep(10)

        update_v1_result = ig_service.update_open_position(
            offer * 1.5, bid * 0.5, open_result["dealId"], version="1"
        )
        assert update_v1_result["dealStatus"] == "ACCEPTED"
        assert update_v1_result["reason"] == "SUCCESS"
        time.sleep(10)

        update_v2_result = ig_service.update_open_position(
            offer * 1.4,
            bid * 0.4,
            open_result["dealId"],
            trailing_stop=True,
            trailing_stop_distance=25.0,
            trailing_stop_increment=10.0,
        )
        assert update_v2_result["dealStatus"] == "ACCEPTED"
        assert update_v2_result["reason"] == "SUCCESS"
        time.sleep(10)

        close_result = ig_service.close_open_position(
            deal_id=open_result["dealId"],
            direction="SELL",
            epic=None,
            expiry="DFB",
            level=None,
            order_type="MARKET",
            quote_id=None,
            size=0.5,
            session=None,
        )
        assert close_result["dealStatus"] == "ACCEPTED"
        assert close_result["reason"] == "SUCCESS"

    @pytest.mark.skipif(not munch_installed, reason="Requires munch")
    def test_create_working_order(self, ig_service: IGService):
        epic = "CS.D.GBPUSD.TODAY.IP"
        market_info = ig_service.fetch_market_by_epic(epic)
        status = market_info.snapshot.marketStatus
        min_bet = market_info.dealingRules.minDealSize.value
        offer = market_info.snapshot.offer
        if status != "TRADEABLE":
            pytest.skip("Skipping create working order test, market not open")

        create_result = ig_service.create_working_order(
            epic=epic,
            direction="BUY",
            currency_code="GBP",
            order_type="LIMIT",
            expiry="DFB",
            guaranteed_stop="false",
            time_in_force="GOOD_TILL_CANCELLED",
            size=min_bet,
            level=offer * 0.9,
            limit_level=None,
            limit_distance=None,
            stop_distance=None,
            stop_level=None,
        )
        assert create_result["dealStatus"] == "ACCEPTED"
        assert create_result["reason"] == "SUCCESS"

        time.sleep(10)

        delete_result = ig_service.delete_working_order(create_result["dealId"])
        assert delete_result["dealStatus"] == "ACCEPTED"
        assert delete_result["reason"] == "SUCCESS"

    @pytest.mark.skipif(not munch_installed, reason="Requires munch")
    def test_create_working_order_guaranteed_stop_loss(self, ig_service: IGService):
        epic = "CS.D.GBPUSD.TODAY.IP"
        market_info = ig_service.fetch_market_by_epic(epic)
        status = market_info.snapshot.marketStatus
        min_bet = market_info.dealingRules.minDealSize.value
        offer = market_info.snapshot.offer
        bid = market_info.snapshot.bid

        logging.info(f"min bet: {min_bet}")
        logging.info(f"offer: {offer}")
        logging.info(f"bid: {bid}")

        if status != "TRADEABLE":
            pytest.skip("Skipping create working order test, market not open")

        create_result = ig_service.create_working_order(
            epic=epic,
            direction="BUY",
            currency_code="GBP",
            order_type="LIMIT",
            expiry="DFB",
            guaranteed_stop="true",
            time_in_force="GOOD_TILL_CANCELLED",
            size=min_bet,
            level=offer * 0.90,
            limit_level=None,
            limit_distance=None,
            stop_distance=200,
            stop_level=None,
        )

        logging.info(
            f"result: {create_result['dealStatus']}, reason {create_result['reason']}"
        )

        assert create_result["dealStatus"] == "ACCEPTED"
        assert create_result["reason"] == "SUCCESS"
        assert create_result["guaranteedStop"]

        time.sleep(10)

        update_result = ig_service.update_working_order(
            good_till_date=None,
            level=offer * 0.85,
            limit_distance=None,
            limit_level=None,
            stop_distance=None,
            stop_level=offer * 0.80,
            guaranteed_stop="true",
            time_in_force="GOOD_TILL_CANCELLED",
            order_type="LIMIT",
            deal_id=create_result["dealId"],
        )

        logging.info(
            f"result: {update_result['dealStatus']}, reason {update_result['reason']}"
        )

        assert update_result["dealStatus"] == "ACCEPTED"
        assert update_result["reason"] == "SUCCESS"
        assert update_result["guaranteedStop"]

        time.sleep(10)

        delete_result = ig_service.delete_working_order(create_result["dealId"])
        assert delete_result["dealStatus"] == "ACCEPTED"
        assert delete_result["reason"] == "SUCCESS"

    def test_fetch_transaction_history(self, ig_service: IGService):
        data = ig_service.fetch_transaction_history()
        assert type(data) is pd.DataFrame

    def test_watchlist_add_market(self, ig_service: IGService, watchlist_id):
        response = ig_service.add_market_to_watchlist(watchlist_id, "MT.D.GC.Month2.IP")
        assert response["status"] == "SUCCESS"

    def test_watchlist_remove_market(self, ig_service: IGService, watchlist_id):
        response = ig_service.remove_market_from_watchlist(
            watchlist_id, "CS.D.GBPUSD.TODAY.IP"
        )
        assert response["status"] == "SUCCESS"

    def test_get_client_apps(self, ig_service: IGService):
        apps_list = ig_service.get_client_apps()
        assert len(apps_list) > 0

    @pytest.mark.skip(reason="endpoint throwing 500 errors - April 2021")
    def test_update_client_app(self, ig_service: IGService):
        result = ig_service.update_client_app(60, 60, config.api_key, "ENABLED")
        print(result)

    def test_logout(self, limited_retrying):
        ig_service = IGService(
            config.username,
            config.password,
            config.api_key,
            config.acc_type,
            retryer=limited_retrying,
        )
        ig_service.create_session()
        ig_service.logout()
        with pytest.raises(Exception) as error:
            print(error)
            ig_service.fetch_accounts()
