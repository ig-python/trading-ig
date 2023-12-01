import logging
import time
from trading_ig import IGService, IGStreamService
from trading_ig.config import config
from trading_ig.streamer.manager import StreamingManager
from sample.sample_utils import crypto_epics  # fx_epics, index_epics, weekend_epics

try:
    from rich.table import Table
    from rich.live import Live
except ImportError:
    print("Rich must be installed for this sample")


def main():
    logging.basicConfig(level=logging.WARNING)

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

    def generate_table(tickers) -> Table:
        table = Table(title="EPIC Prices")
        table.add_column("EPIC")
        table.add_column("Bid", justify="right")
        table.add_column("Offer", justify="right")
        table.add_column("Last traded price", justify="right")
        table.add_column("Last traded volume", justify="right")
        table.add_column("Incremental volume", justify="right")
        table.add_column("Mid open", justify="right")
        table.add_column("Change since open", justify="right")
        table.add_column("Daily % change", justify="right")
        table.add_column("Day high", justify="right")
        table.add_column("Day low", justify="right")
        table.add_column("Timestamp")

        for ticker in tickers:
            table.add_row(
                f"{ticker.epic}",
                f"{ticker.bid:.2f}",
                f"{ticker.offer:.2f}",
                f"{ticker.last_traded_price:.2f}",
                f"{ticker.last_traded_volume}",
                f"{ticker.incr_volume}",
                f"{ticker.day_open_mid:.2f}",
                f"{ticker.day_net_change_mid:.2f}",
                f"{ticker.day_percent_change_mid:.2f}",
                f"{ticker.day_high:.2f}",
                f"{ticker.day_low:.2f}",
                f"{ticker.timestamp.strftime('%Y-%m-%d %H:%M:%S') if ticker.timestamp else ''}",
            )

        return table

    with Live(generate_table(tickers), refresh_per_second=4) as live:
        for _ in range(100):
            time.sleep(0.4)
            live.update(generate_table(tickers))

    for epic in crypto_epics:
        sm.stop_tick_subscription(epic)


if __name__ == "__main__":
    main()
