import logging
import time
from trading_ig import IGService, IGStreamService
from trading_ig.config import config
from trading_ig.streamer.manager import StreamingManager
from sample.sample_utils import crypto_epics  # fx_epics, index_epics, weekend_epics


def main():
    logging.basicConfig(level=logging.INFO)

    ig_service = IGService(
        config.username,
        config.password,
        config.api_key,
        config.acc_type,
        acc_number=config.acc_number,
    )

    ig = IGStreamService(ig_service)
    ig.create_session(version="3")
    sm = StreamingManager(ig)

    tickers = []
    for epic in crypto_epics:  # fx_epics, index_epics, crypto_epics
        sm.start_tick_subscription(epic)
        tickers.append(sm.ticker(epic))

    for idx in range(0, 10):
        for ticker in tickers:
            print(ticker)
        time.sleep(0.5)

    sm.stop_subscriptions()


if __name__ == "__main__":
    main()
