from trading_ig.rest import IGService
from trading_ig.config import config
import pandas as pd
import datetime
import pytest
from random import randint
from ratelimit import limits, sleep_and_retry


@pytest.fixture(scope="module")
def ig_service():
    """test fixture logs into IG with the configured credentials"""
    if config.acc_type == 'LIVE':
        pytest.fail('this integration test should not be executed with a LIVE account')
    ig_service = IGService(config.username, config.password,
                           config.api_key, config.acc_type)
    ig_service.create_session()
    return ig_service


@pytest.fixture(scope="module")
def top_level_nodes(ig_service):
    """test fixture gets the top level navigation nodes"""
    response = ig_service.fetch_top_level_navigation_nodes()
    return response["nodes"]


@pytest.fixture(scope="module")
def watchlists(ig_service):
    """test fixture gets all watchlists"""
    return ig_service.fetch_all_watchlists()


class TestIntegration:

    def test_fetch_accounts(self, ig_service):
        response = ig_service.fetch_accounts()
        preferred = response.loc[response["preferred"]]
        assert all(preferred["balance"] > 0)

    def test_fetch_account_activity_by_period(self, ig_service):
        response = ig_service.fetch_account_activity_by_period(10000)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_transaction_history_by_type_and_period(self, ig_service):
        response = ig_service.fetch_transaction_history_by_type_and_period(10000, "ALL")
        assert isinstance(response, pd.DataFrame)

    def test_fetch_open_positions(self, ig_service):
        response = ig_service.fetch_open_positions()
        assert isinstance(response, pd.DataFrame)

    def test_fetch_working_orders(self, ig_service):
        response = ig_service.fetch_working_orders()
        assert isinstance(response, pd.DataFrame)

    def test_fetch_top_level_navigation_nodes(self, top_level_nodes):
        assert isinstance(top_level_nodes, pd.DataFrame)

    def test_fetch_client_sentiment_by_instrument(self, ig_service, top_level_nodes):
        rand_index = randint(0, len(top_level_nodes) - 1)
        node_id = top_level_nodes.iloc[rand_index]["id"]
        response = ig_service.fetch_client_sentiment_by_instrument(node_id)
        assert isinstance(response, dict)

    def test_fetch_sub_nodes_by_node(self, ig_service, top_level_nodes):
        rand_index = randint(0, len(top_level_nodes) - 1)
        response = ig_service.fetch_sub_nodes_by_node(rand_index)
        assert isinstance(response["markets"], pd.DataFrame)
        assert isinstance(response["nodes"], pd.DataFrame)

    def test_fetch_all_watchlists(self, watchlists):
        assert isinstance(watchlists, pd.DataFrame)
        default = watchlists[watchlists["defaultSystemWatchlist"]]
        assert any(default["id"] == "Popular Markets")

    def test_fetch_watchlist_markets(self, ig_service, watchlists):
        rand_index = randint(0, len(watchlists) - 1)
        watchlist_id = watchlists.iloc[rand_index]["id"]
        response = ig_service.fetch_watchlist_markets(watchlist_id)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_market_by_epic(self, ig_service):
        response = ig_service.fetch_market_by_epic("CS.D.EURUSD.MINI.IP")
        assert isinstance(response, dict)

    def test_search_markets(self, ig_service):
        search_term = "EURUSD"
        response = ig_service.search_markets(search_term)
        assert isinstance(response, pd.DataFrame)

    def test_fetch_historical_prices_by_epic_and_numpoints(self, ig_service):
        response = ig_service.fetch_historical_prices_by_epic_and_num_points(
            "CS.D.EURUSD.MINI.IP", "H", 4
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert len(response["prices"]) == 4

    def test_fetch_historical_prices_by_epic_and_date_range(self, ig_service):
        response = ig_service.fetch_historical_prices_by_epic_and_date_range(
            "CS.D.EURUSD.MINI.IP", "D", "2020:09:01-00:00:00", "2020:09:04-23:59:59"
        )
        assert isinstance(response["allowance"], dict)
        assert isinstance(response["prices"], pd.DataFrame)
        assert len(response["prices"]) == 4

    def test_fetch_historical_prices_by_epic_dates(self, ig_service):
        result = self.wrap_rate_limit_hist(
            ig_service,
            epic='MT.D.GC.Month2.IP',
            resolution='D',
            start_date='2020-09-01T00:00:00',
            end_date='2020-09-04T23:59:59')

        prices = result['prices']
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)
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

    def test_fetch_historical_prices_by_epic_numpoints(self, ig_service):
        result = self.wrap_rate_limit_hist(
            ig_service,
            epic='MT.D.GC.Month2.IP',
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

    def test_fetch_historical_prices_by_epic_numpoints_default_paged(
            self,
            ig_service):
        result = self.wrap_rate_limit_hist(
            ig_service,
            epic='MT.D.GC.Month2.IP',
            resolution='W',
            numpoints=21)

        # assert default paged row count
        assert result['prices'].shape[0] == 21
        assert result['metadata']['pageData']['pageNumber'] == 2

    def test_fetch_historical_prices_by_epic_numpoints_custom_paged(
            self,
            ig_service):
        result = self.wrap_rate_limit_hist(
            ig_service,
            epic='MT.D.GC.Month2.IP',
            resolution='W',
            numpoints=6,
            pagesize=2)

        # assert default paged row count
        assert result['prices'].shape[0] == 6
        assert result['metadata']['pageData']['pageNumber'] == 3

    @sleep_and_retry
    @limits(calls=30, period=60)
    def wrap_rate_limit_hist(self, ig_service, epic, resolution, start_date=None, end_date=None,
                             numpoints=None, pagesize=None, wait=2):
        return ig_service.fetch_historical_prices_by_epic(
            epic=epic,
            resolution=resolution,
            start_date=start_date,
            end_date=end_date,
            numpoints=numpoints,
            pagesize=pagesize,
            wait=wait)
