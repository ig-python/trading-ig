from dataclasses import dataclass
from datetime import datetime
from trading_ig.lightstreamer import Subscription
from .objects import nan, StreamObject


class TickerSubscription(Subscription):
    """Represents a subscription for tick prices"""

    TICKER_FIELDS = [
        "BID",
        "OFR",
        "LTP",
        "LTV",
        "TTV",
        "UTM",
        "DAY_OPEN_MID",
        "DAY_NET_CHG_MID",
        "DAY_PERC_CHG_MID",
        "DAY_HIGH",
        "DAY_LOW",
    ]

    def __init__(self, epic: str):

        super().__init__(
            mode="DISTINCT",
            items=[f"CHART:{epic}:TICK"],
            fields=self.TICKER_FIELDS,
        )

    def __repr__(self) -> str:
        return f"TickSubscription with {len(self.item_names)} epics"


@dataclass
class Ticker(StreamObject):
    epic: str
    timestamp: datetime = None
    bid: float = nan
    offer: float = nan
    last_traded_price: float = nan
    last_traded_volume: int = 0
    incr_volume: int = 0
    day_open_mid: float = nan
    day_net_change_mid: float = nan
    day_percent_change_mid: float = nan
    day_high: float = nan
    day_low: float = nan

    def __init__(self, epic):
        self.epic = epic

    def __repr__(self) -> str:
        return (
            f"{self.epic}: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
            f"{self.bid} {self.offer} {self.last_traded_price} "
            f"{self.last_traded_volume} {self.incr_volume} {self.day_open_mid} "
            f"{self.day_net_change_mid} {self.day_percent_change_mid}% {self.day_high} "
            f"{self.day_low}"
        )

    def populate(self, values):
        # print(f"ticker populating: {values}")
        self.set_timestamp_by_name("timestamp", values, "UTM")
        self.set_by_name("bid", values, "BID", float)
        self.set_by_name("offer", values, "OFR", float)
        self.set_by_name("last_traded_price", values, "LTP", float)
        self.set_by_name("last_traded_volume", values, "LTV", int)
        self.set_by_name("incr_volume", values, "TTV", int)
        self.set_by_name("day_open_mid", values, "DAY_OPEN_MID", float)
        self.set_by_name("day_net_change_mid", values, "DAY_NET_CHG_MID", float)
        self.set_by_name("day_percent_change_mid", values, "DAY_PERC_CHG_MID", float)
        self.set_by_name("day_high", values, "DAY_HIGH", float)
        self.set_by_name("day_low", values, "DAY_LOW", float)

    @classmethod
    def identifier(cls, name):
        epic = name.split(":")[1]
        return epic
