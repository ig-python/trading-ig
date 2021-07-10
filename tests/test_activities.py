from trading_ig.rest import IGService
import responses
import json
import pandas as pd
from datetime import datetime, timedelta
import re


class TestActivities:

    """
    unit tests for activities
    """

    @responses.activate
    def test_activities_by_period(self):

        # test_activities_by_period

        with open('tests/data/activities_v1.json', 'r') as file:
            response_body = json.loads(file.read())

        responses.add(responses.GET,
                      re.compile('https://demo-api.ig.com/gateway/deal/history/activity/.+'),
                      match_querystring=False,
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json=response_body,
                      status=200)

        ig_service = IGService('username', 'password', 'api_key', 'DEMO')
        result = ig_service.fetch_account_activity_by_period(10000000)

        # we expect a pd.DataFrame with 17 columns and 3 rows
        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == 3
        assert result.shape[1] == 17

    @responses.activate
    def test_activities_by_date(self):

        # fetch_account_activity_by_date

        with open('tests/data/activities_v1.json', 'r') as file:
            response_body = json.loads(file.read())

        url = "https://demo-api.ig.com/gateway/deal/"
        date_pat = '[0-9]{2}-[0-9]{2}-[0-9]{4}' # NOT a very god regexp for dates will suffice here

        responses.add(responses.GET,
                      re.compile(f"{url}history/activity/{date_pat}/{date_pat}"),
                      match_querystring=False,
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json=response_body,
                      status=200)

        ig_service = IGService('username', 'password', 'api_key', 'DEMO')
        to_date = datetime.now()
        from_date = to_date - timedelta(days=7)
        result = ig_service.fetch_account_activity_by_date(from_date, to_date)

        # we expect a pd.DataFrame with 17 columns and 3 rows
        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == 3
        assert result.shape[1] == 17


