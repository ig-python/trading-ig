#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
IG Markets Stream API sample with Python
2015 FemtoTrader
"""

import logging

from trading_ig import IGService, IGStreamService
from trading_ig.config import config
from trading_ig.lightstreamer import Subscription


# A simple function acting as a Subscription listener
def on_prices_update(item_update):
    # print("price: %s " % item_update)
    print(
        "{stock_name:<19}: Time {UPDATE_TIME:<8} - "
        "Bid {BID:>5} - Ask {OFFER:>5}".format(
            stock_name=item_update["name"], **item_update["values"]
        )
    )


def on_account_update(balance_update):
    print("balance: %s " % balance_update)


def main():
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    ig_service = IGService(
        config.username, config.password, config.api_key, config.acc_type, acc_number=config.acc_number
    )

    ig_stream_service = IGStreamService(ig_service)
    ig_stream_service.create_session()
    #ig_stream_service.create_session(version='3')

    # Making a new Subscription in MERGE mode
    subscription_prices = Subscription(
        mode="MERGE",
        #items=["L1:CS.D.GBPUSD.CFD.IP", "L1:CS.D.USDJPY.CFD.IP"], # sample CFD epics
        items=["L1:CS.D.GBPUSD.TODAY.IP", "L1:IX.D.FTSE.DAILY.IP"], # sample spreadbet epics
        fields=["UPDATE_TIME", "BID", "OFFER", "CHANGE", "MARKET_STATE"],
    )

    # Adding the "on_price_update" function to Subscription
    subscription_prices.addlistener(on_prices_update)

    # Registering the Subscription
    sub_key_prices = ig_stream_service.ls_client.subscribe(subscription_prices)

    # Making an other Subscription in MERGE mode
    subscription_account = Subscription(
        mode="MERGE", items=["ACCOUNT:" + config.acc_number], fields=["AVAILABLE_CASH"],
    )

    # Adding the "on_balance_update" function to Subscription
    subscription_account.addlistener(on_account_update)

    # Registering the Subscription
    sub_key_account = ig_stream_service.ls_client.subscribe(subscription_account)

    input(
        "{0:-^80}\n".format(
            "HIT CR TO UNSUBSCRIBE AND DISCONNECT FROM \
    LIGHTSTREAMER"
        )
    )

    # Disconnecting
    ig_stream_service.disconnect()


if __name__ == "__main__":
    main()
