from trading_ig.rest import IGService
import responses
import json
import pandas as pd


class TestPositions:

    """
    unit tests for position methods
    """

    @responses.activate
    def test_v2_happy_path(self):
        """
        fetch_open_positions() (v2)
        """

        with open("tests/data/positions_v2.json", "r") as file:
            response_body = json.loads(file.read())

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/positions",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=response_body,
            status=200,
        )

        ig_service = IGService("username", "password", "api_key", "DEMO")
        pos = ig_service.fetch_open_positions()

        assert isinstance(pos, pd.DataFrame)
        assert pos.shape[0] == 2
        assert pos.shape[1] == 32
        assert pos.iloc[0]["createdDateUTC"] == "2020-06-01T12:00:00"
        assert pos.iloc[0]["size"] == 10
        assert pos.iloc[1]["level"] == 1800.0
        assert pos.iloc[0]["offer"] == 16999.0
        assert pos.iloc[1]["bid"] == 1865.3

    @responses.activate
    def test_v1_happy_path(self):
        """
        fetch_open_positions() (v1)
        """

        with open("tests/data/positions_v1.json", "r") as file:
            response_body = json.loads(file.read())

        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/positions",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=response_body,
            status=200,
        )

        ig_service = IGService("username", "password", "api_key", "DEMO")
        pos = ig_service.fetch_open_positions(version="1")

        assert isinstance(pos, pd.DataFrame)
        assert pos.shape[0] == 2
        assert pos.shape[1] == 29
        assert pos.iloc[0]["createdDate"] == "2020/06/01 12:00:00:000"
        assert pos.iloc[0]["dealSize"] == 10
        assert pos.iloc[1]["openLevel"] == 1800.0
        assert pos.iloc[0]["offer"] == 16999.0
        assert pos.iloc[1]["bid"] == 1865.3
