from trading_ig.rest import IGService
import responses
import json
import pandas as pd
import datetime
import pytest

"""
unit tests for historical prices methods with flat output formatting
"""


class TestHistoricalPricesFlat:
    @responses.activate
    def test_historical_prices_v3_defaults_happy(self):
        # fetch_historical_prices v3 - default params

        with open("tests/data/historic_prices.json", "r") as file:
            response_body = json.loads(file.read())

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=response_body,
            status=200,
        )

        ig_service = IGService("username", "password", "api_key", "DEMO")
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP", format=ig_service.flat_prices
        )
        prices = result["prices"]

        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # with no other params, default returns 10 rows at MINUTE resolution
        assert prices.shape[0] == 10
        assert prices.shape[1] == 9

        # assert time series rows are 1 minute apart
        prices["tvalue"] = prices.index
        prices["delta"] = prices["tvalue"] - prices["tvalue"].shift()
        assert any(prices["delta"].dropna() == datetime.timedelta(minutes=1))

    @responses.activate
    def test_historical_prices_v3_datetime_happy(self):
        # fetch_historical_prices v3 - between two dates, daily resolution

        with open("tests/data/historic_prices_dates.json", "r") as file:
            response_body = json.loads(file.read())

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=response_body,
            status=200,
        )

        ig_service = IGService("username", "password", "api_key", "DEMO")
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP",
            resolution="D",
            start_date="2020-09-01T00:00:00",
            end_date="2020-09-04T23:59:59",
            format=ig_service.flat_prices,
        )

        prices = result["prices"]
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 4
        assert prices.shape[1] == 9

        # assert time series rows are 1 day apart
        prices["tvalue"] = prices.index
        prices["delta"] = prices["tvalue"] - prices["tvalue"].shift()
        assert any(prices["delta"].dropna() == datetime.timedelta(days=1))

        # assert default paging
        assert result["metadata"]["pageData"]["pageSize"] == 20
        assert result["metadata"]["pageData"]["pageNumber"] == 1
        assert result["metadata"]["pageData"]["totalPages"] == 1

    @responses.activate
    def test_historical_prices_v3_num_points_happy(self):
        # fetch_historical_prices v3 - number of data points, weekly resolution

        with open("tests/data/historic_prices_num_points.json", "r") as file:
            response_body = json.loads(file.read())

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=response_body,
            status=200,
        )

        ig_service = IGService("username", "password", "api_key", "DEMO")
        result = ig_service.fetch_historical_prices_by_epic(
            epic="MT.D.GC.Month2.IP",
            resolution="W",
            numpoints=10,
            format=ig_service.flat_prices,
        )

        prices = result["prices"]
        assert isinstance(result, dict)
        assert isinstance(prices, pd.DataFrame)

        # assert DataFrame shape
        assert prices.shape[0] == 10
        assert prices.shape[1] == 9

        # assert time series rows are 1 week apart
        prices["tvalue"] = prices.index
        prices["delta"] = prices["tvalue"] - prices["tvalue"].shift()
        assert any(prices["delta"].dropna() == datetime.timedelta(weeks=1))

    @responses.activate
    def test_historical_prices_v3_num_points_bad_numpoints(self):
        # fetch_historical_prices v3 - number of data points, invalid numpoints

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json={
                "errorCode": "Unable to convert value=3.14159 to type= Integer int"
            },  # noqa
            status=400,
        )

        with pytest.raises(Exception):
            ig_service = IGService("username", "password", "api_key", "DEMO")
            result = ig_service.fetch_historical_prices_by_epic(
                epic="MT.D.GC.Month2.IP",
                resolution="X",
                numpoints=3.14159,
                format=ig_service.flat_prices,
            )
            assert result["errorCode"].startswith("Unable to convert value")

    @responses.activate
    def test_historical_prices_v3_num_points_bad_resolution(self):
        # fetch_historical_prices v3 - number of data points, invalid resolution

        with open("tests/data/historic_prices_num_points.json", "r") as file:
            response_body = json.loads(file.read())

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.GC.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=response_body,
            status=200,
        )

        with pytest.raises(ValueError) as excinfo:
            ig_service = IGService("username", "password", "api_key", "DEMO")
            ig_service.fetch_historical_prices_by_epic(
                epic="MT.D.GC.Month2.IP",
                resolution="X",
                numpoints=10,
                format=ig_service.flat_prices,
            )
            assert "Invalid frequency" in str(excinfo.value)

    @responses.activate
    def test_historical_prices_v3_bad_epic(self):
        # fetch_historical_prices v3 - bad epic

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.X.Month1.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json={"errorCode": "error.error.price-history.io-error"},
            status=404,
        )

        with pytest.raises(Exception):
            ig_service = IGService("username", "password", "api_key", "DEMO")
            result = ig_service.fetch_historical_prices_by_epic(
                epic="MT.D.X.Month1.IP", format=ig_service.flat_prices
            )
            assert result["errorCode"] == "error.error.price-history.io-error"

    @responses.activate
    def test_historical_prices_v3_bad_date_format(self):
        # fetch_historical_prices v3 - bad date format

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.XX.Month1.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json={"errorCode": "Unable to parse datetime=2020/09/01T00:00:00"},
            status=400,
        )

        with pytest.raises(Exception):
            ig_service = IGService("username", "password", "api_key", "DEMO")
            result = ig_service.fetch_historical_prices_by_epic(
                epic="MT.D.GC.Month2.IP",
                resolution="D",
                start_date="2020/09/01T00:00:00",
                end_date="2020-09-04T23:59:59",
                format=ig_service.flat_prices,
            )
            assert result["errorCode"].startswith("Unable to parse datetime")

    @responses.activate
    def test_historical_prices_v3_bad_date_order(self):
        # fetch_historical_prices v3 - bad date order

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/MT.D.XX.Month1.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json={"errorCode": "error.invalid.daterange"},
            status=400,
        )

        with pytest.raises(Exception):
            ig_service = IGService("username", "password", "api_key", "DEMO")
            result = ig_service.fetch_historical_prices_by_epic(
                epic="MT.D.GC.Month2.IP",
                resolution="D",
                start_date="2020-09-04T23:59:59",
                end_date="2020/09/01T00:00:00",
                format=ig_service.flat_prices,
            )
            assert result["errorCode"] == "error.invalid.daterange"
