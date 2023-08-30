from trading_ig.rest import IGService
import responses
import json
import time

"""
unit tests for rate limiter
"""


class TestRateLimiter:
    @responses.activate
    def test_rate_limiter_non_trading_req(self):
        with open("tests/data/session.json", "r") as file:
            session_response_body = json.loads(file.read())

        responses.add(
            responses.POST,
            "https://demo-api.ig.com/gateway/deal/session",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=session_response_body,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/session",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=session_response_body,
            status=200,
        )

        with open("tests/data/application.json", "r") as file:
            app_response_body = json.loads(file.read())

        responses.add(
            responses.POST,
            "https://demo-api.ig.com/gateway/deal/operations/application",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=app_response_body,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/operations/application",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=app_response_body,
            status=200,
        )

        with open("tests/data/markets_epic.json", "r") as file:
            mkts_epic_response_body = json.loads(file.read())

        responses.add(
            responses.POST,
            "https://demo-api.ig.com/gateway/deal/markets/CO.D.CFI.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=mkts_epic_response_body,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/markets/CO.D.CFI.Month2.IP",
            headers={"CST": "abc123", "X-SECURITY-TOKEN": "xyz987"},
            json=mkts_epic_response_body,
            status=200,
        )

        ig_service = IGService(
            "username", "password", "api_key", "DEMO", use_rate_limiter=True
        )

        ig_service.create_session()

        # empty the bucket queue (len=1), before we start timing things
        ig_service.fetch_market_by_epic("CO.D.CFI.Month2.IP")

        times = []
        for i in range(3):
            time_last = time.time()
            ig_service.fetch_market_by_epic("CO.D.CFI.Month2.IP")
            times.append(time.time() - time_last)

        ig_service.logout()

        av_time = sum(times) / len(times)

        expected_av = 60.0 / app_response_body[0]["allowanceAccountOverall"]

        time_tolerance = 0.2

        assert av_time >= expected_av
        assert av_time < expected_av + time_tolerance
