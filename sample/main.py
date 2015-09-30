#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
IG Markets Stream API with Python
2015 FemtoTrader
"""

import time

from trading_ig_config import config
from trading_ig import IGService
from trading_ig_stream import igls

# Tell the user when the Lighstreamer connection state changes
def on_state(state):
    print('New state:', state)
    igls.LOG.debug("New state: %s" % state)

# Process a lighstreamer price update
def process_price_update(item, myUpdateField, item_ids):
    #print("price update for %s" % myUpdateField)
    print("price update for %s= %s" % (item_ids, myUpdateField))

# Process an update of the users trading account balance
def process_balance_update(item, myUpdateField):
    print("balance update = %s" % myUpdateField)

if __name__ == '__main__':
    ig_service = IGService(config.username, config.password, config.api_key, config.acc_type)
    ig_session = ig_service.create_session()
    cst = ig_service.crud_session.CLIENT_TOKEN
    xsecuritytoken = ig_service.crud_session.SECURITY_TOKEN
    lightstreamerEndpoint = ig_session[u'lightstreamerEndpoint']
    clientId = ig_session[u'clientId']
    accounts = ig_session[u'accounts']
    # Depending on how many accounts you have with IG the '0' may need to change to select the correct one (spread bet, CFD account etc)
    accountId = accounts[0][u'accountId']

    client = igls.LsClient(lightstreamerEndpoint + "/lightstreamer/")
    client.on_state.listen(on_state)
    client.create_session(username=accountId, password='CST-%s|XST-%s' % (cst, xsecuritytoken), adapter_set='')

    lst_item_ids = ['L1:CS.D.GBPUSD.CFD.IP', 'L1:CS.D.USDJPY.CFD.IP']
    for item_id in lst_item_ids:
        priceTable = igls.Table(client,
            mode=igls.MODE_MERGE,
            item_ids=item_id,
            schema='UPDATE_TIME BID OFFER CHANGE MARKET_STATE',
            item_factory=lambda row: tuple(float(v) for v in row)
        )
        priceTable.on_update.listen(process_price_update)

    balanceTable = igls.Table(client,
        mode=igls.MODE_MERGE,
        item_ids='ACCOUNT:'+accountId,
        schema='AVAILABLE_CASH',
        item_factory=lambda row: tuple(string(v) for v in row))

    balanceTable.on_update.listen(process_balance_update)

    delay = 10
    while True:
        time.sleep(delay)
        print("sleep %d" % delay)
