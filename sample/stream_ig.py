#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
IG Markets Stream API sample with Python
2015 FemtoTrader
"""

import time
import sys
import traceback
import logging

from trading_ig import (IGService, IGStreamService)
from trading_ig.config import config
from trading_ig.lightstreamer import Subscription


# A simple function acting as a Subscription listener
def on_prices_update(item_update):
    # print("price: %s " % item_update)
    print("{stock_name:<19}: Time {UPDATE_TIME:<8} - "
          "Bid {BID:>5} - Ask {OFFER:>5}".format(stock_name=item_update["name"], **item_update["values"]))

def on_account_update(balance_update):
    print("balance: %s " % balance_update)

def main():
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    ig_service = IGService(config.username, config.password, config.api_key, config.acc_type)

    ig_stream_service = IGStreamService(ig_service)
    ig_session = ig_stream_service.create_session()
    # Ensure configured account is selected
    accounts = ig_session[u'accounts']
    for account in accounts:
        if account[u'accountId'] == config.acc_number:
            accountId = account[u'accountId']
        else:
            print('Account not found: {0}'.format(config.acc_number))
            accountId = None
    ig_stream_service.connect(accountId)

    # Making a new Subscription in MERGE mode
    subcription_prices = Subscription(
        mode="MERGE",
        items=['L1:CS.D.GBPUSD.CFD.IP', 'L1:CS.D.USDJPY.CFD.IP'],
        fields=["UPDATE_TIME", "BID", "OFFER", "CHANGE", "MARKET_STATE"],
        )
        #adapter="QUOTE_ADAPTER")


    # Adding the "on_price_update" function to Subscription
    subcription_prices.addlistener(on_prices_update)

    # Registering the Subscription
    sub_key_prices = ig_stream_service.ls_client.subscribe(subcription_prices)


    # Making an other Subscription in MERGE mode
    subscription_account = Subscription(
        mode="MERGE",
        items='ACCOUNT:'+accountId,
        fields=["AVAILABLE_CASH"],
        )
    #    #adapter="QUOTE_ADAPTER")

    # Adding the "on_balance_update" function to Subscription
    subscription_account.addlistener(on_account_update)

    # Registering the Subscription
    sub_key_account = ig_stream_service.ls_client.subscribe(subscription_account)

    input("{0:-^80}\n".format("HIT CR TO UNSUBSCRIBE AND DISCONNECT FROM \
    LIGHTSTREAMER"))

    # Disconnecting
    ig_stream_service.disconnect()

if __name__ == '__main__':
    main()
