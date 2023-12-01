from trading_ig.rest import IGService, ApiExceededException, TokenInvalidException
import responses
from responses import Response
import json
import tenacity
from tenacity import Retrying
import pandas as pd


class TestRetry:
    # test_retry

    @responses.activate
    def test_exceed_retry(self):
        with open("tests/data/accounts_balances.json", "r") as file:
            response_body = json.loads(file.read())

        url = "https://demo-api.ig.com/gateway/deal/accounts"
        headers = {"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"}
        api_exceeded = {"errorCode": "error.public-api.exceeded-api-key-allowance"}
        account_exceeded = {"errorCode": "error.public-api.exceeded-account-allowance"}
        trading_exceeded = {
            "errorCode": "error.public-api.exceeded-account-trading-allowance"
        }

        responses.add(
            Response(method="GET", url=url, headers={}, json=api_exceeded, status=403)
        )
        responses.add(
            Response(
                method="GET", url=url, headers={}, json=account_exceeded, status=403
            )
        )
        responses.add(
            Response(
                method="GET", url=url, headers={}, json=trading_exceeded, status=403
            )
        )
        responses.add(
            Response(
                method="GET", url=url, headers=headers, json=response_body, status=200
            )
        )

        ig_service = IGService(
            "username",
            "password",
            "api_key",
            "DEMO",
            retryer=Retrying(
                wait=tenacity.wait_exponential(),
                retry=tenacity.retry_if_exception_type(ApiExceededException),
            ),
        )

        result = ig_service.fetch_accounts()

        assert responses.assert_call_count(url, 4) is True
        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0]["accountId"] == "XYZ987"

    @responses.activate
    def test_token_retry(self):
        with open("tests/data/accounts_balances.json", "r") as file:
            response_body = json.loads(file.read())

        url = "https://demo-api.ig.com/gateway/deal/accounts"
        headers = {"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"}
        client_token_error = {"errorCode": "error.security.client-token-invalid"}
        oauth_token_error = {"errorCode": "error.security.oauth-token-invalid"}

        responses.add(
            Response(
                method="GET", url=url, headers={}, json=client_token_error, status=403
            )
        )
        responses.add(
            Response(
                method="GET", url=url, headers={}, json=oauth_token_error, status=403
            )
        )
        responses.add(
            Response(
                method="GET", url=url, headers={}, json=client_token_error, status=403
            )
        )
        responses.add(
            Response(
                method="GET", url=url, headers=headers, json=response_body, status=200
            )
        )

        ig_service = IGService(
            "username",
            "password",
            "api_key",
            "DEMO",
            retryer=Retrying(
                wait=tenacity.wait_exponential(),
                retry=tenacity.retry_if_exception_type(TokenInvalidException),
            ),
        )

        result = ig_service.fetch_accounts()

        assert responses.assert_call_count(url, 4) is True
        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0]["accountId"] == "XYZ987"

    @responses.activate
    def test_all_retry(self):
        with open("tests/data/accounts_balances.json", "r") as file:
            response_body = json.loads(file.read())

        url = "https://demo-api.ig.com/gateway/deal/accounts"
        headers = {"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"}
        client_token_error = {"errorCode": "error.security.client-token-invalid"}
        api_exceeded = {"errorCode": "error.public-api.exceeded-api-key-allowance"}

        responses.add(
            Response(
                method="GET", url=url, headers={}, json=client_token_error, status=403
            )
        )
        responses.add(
            Response(method="GET", url=url, headers={}, json=api_exceeded, status=403)
        )
        responses.add(
            Response(
                method="GET", url=url, headers=headers, json=response_body, status=200
            )
        )

        ig_service = IGService(
            "username",
            "password",
            "api_key",
            "DEMO",
            retryer=Retrying(
                wait=tenacity.wait_exponential(),
                retry=tenacity.retry_if_exception_type(
                    (ApiExceededException, TokenInvalidException)
                ),
            ),
        )

        result = ig_service.fetch_accounts()

        assert responses.assert_call_count(url, 3) is True
        assert isinstance(result, pd.DataFrame)
        assert result.iloc[0]["accountId"] == "XYZ987"
