from trading_ig.rest import IGService
import responses
import json
import pandas as pd

"""
unit tests for accounts methods
"""


class TestAccounts:

    # fetch_accounts

    @responses.activate
    def test_fetch_accounts_happy(self):

        with open('tests/data/accounts_balances.json', 'r') as file:
            response_body = json.loads(file.read())

        responses.add(responses.GET, 'https://demo-api.ig.com/gateway/deal/accounts',
                      headers={'CST': 'abc123', 'X-SECURITY-TOKEN': 'xyz987'},
                      json=response_body,
                      status=200)

        ig_service = IGService('username', 'password', 'api_key', 'DEMO')
        ig_service.crud_session.HEADERS["LOGGED_IN"] = {}
        result = ig_service.fetch_accounts()

        pd.set_option('display.max_columns', 13)
        print(result)

        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0]['accountId'] == 'XYZ987'
        assert result.iloc[0]['balance'] == 1000.0
        assert result.iloc[1]['accountId'] == 'ABC123'
        assert pd.isna(result.iloc[1]['balance'])
        assert pd.isna(result.iloc[1]['deposit'])
