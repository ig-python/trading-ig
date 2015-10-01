#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
IG Markets Stream API with Python
2015 FemtoTrader
"""

import sys
import traceback
import logging
from trading_ig_stream.lightstreamer import LSClient, Subscription
import trading_ig_stream.compat as compat

import time

from trading_ig import IGService
from trading_ig.config import ConfigEnvVar
#from trading_ig_config import config

# A simple function acting as a Subscription listener
def on_price_update(item_update):
    #print("price: %s " % item_update)
    print("{stock_name:<19}: Time {UPDATE_TIME:<8} - "
          "Bid {BID:>5} - Ask {OFFER:>5}".format(stock_name=item_update["name"], **item_update["values"]))

def on_balance_update(balance_update):
    print("balance: %s " % balance_update)

def main():
    logging.basicConfig(level=logging.INFO)
    #logging.basicConfig(level=logging.DEBUG)

    config = ConfigEnvVar("IG_SERVICE")
    ig_service = IGService(config.username, config.password, config.api_key, config.acc_type)
    ig_session = ig_service.create_session()
    cst = ig_service.crud_session.CLIENT_TOKEN
    xsecuritytoken = ig_service.crud_session.SECURITY_TOKEN
    lightstreamerEndpoint = ig_session[u'lightstreamerEndpoint']
    clientId = ig_session[u'clientId']
    accounts = ig_session[u'accounts']
    # Depending on how many accounts you have with IG the '0' may need to change to select the correct one (spread bet, CFD account etc)
    accountId = accounts[0][u'accountId']
    password = 'CST-%s|XST-%s' % (cst, xsecuritytoken)

    # Establishing a new connection to Lightstreamer Server
    print("Starting connection with %s" % lightstreamerEndpoint)
    #lightstreamer_client = LSClient("http://localhost:8080", "DEMO")
    #lightstreamer_client = LSClient("http://push.lightstreamer.com", "DEMO")
    lightstreamer_client = LSClient(lightstreamerEndpoint, adapter_set="", user=accountId, password=password)
    try:
        lightstreamer_client.connect()
    except Exception as e:
        print("Unable to connect to Lightstreamer Server")
        print(traceback.format_exc())
        sys.exit(1)

    # Making a new Subscription in MERGE mode
    subscription = Subscription(
        mode="MERGE",
        items=['L1:CS.D.GBPUSD.CFD.IP', 'L1:CS.D.USDJPY.CFD.IP'],
        fields=["UPDATE_TIME", "BID", "OFFER", "CHANGE", "MARKET_STATE"],
        )
        #adapter="QUOTE_ADAPTER")


    # Adding the "on_item_update" function to Subscription
    subscription.addlistener(on_price_update)

    # Registering the Subscription
    sub_key_prices = lightstreamer_client.subscribe(subscription)


    # Making an other Subscription in MERGE mode
    subscription = Subscription(
        mode="MERGE",
        items='ACCOUNT:'+accountId,
        fields=["AVAILABLE_CASH"],
        )
    #    #adapter="QUOTE_ADAPTER")


    # Adding the "on_item_update" function to Subscription
    subscription.addlistener(on_balance_update)

    # Registering the Subscription
    sub_key_balance = lightstreamer_client.subscribe(subscription)

    compat.wait_for_input("{0:-^80}\n".format("HIT CR TO UNSUBSCRIBE AND DISCONNECT FROM \
    LIGHTSTREAMER"))

    # Unsubscribing from Lightstreamer by using the subscription key
    #lightstreamer_client.unsubscribe(sub_key_prices)
    #lightstreamer_client.unsubscribe(sub_key_balance)
    lightstreamer_client.unsubscribe()

    # Disconnecting
    lightstreamer_client.disconnect()

if __name__ == '__main__':
    main()
