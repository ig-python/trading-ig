#!/usr/bin/env python
#-*- coding:utf-8 -*-

# IG API Trader

from trading_ig_stream import igls
import requests, json, time
from trading_ig_config import config

if config.acc_type.upper() == "DEMO":
    BASEURL = 'https://demo-api.ig.com/gateway/deal'
elif config.acc_type.upper() == "LIVE":
    BASEURL = 'https://api.ig.com/gateway/deal'
else:
    raise(NotImplementedError("acc_type is %r but it should be either 'DEMO' or 'LIVE'" % config.acc_type))

headers = {
    'content-type': 'application/json; charset=UTF-8',
    'Accept': 'application/json; charset=UTF-8',
    'X-IG-API-KEY': config.api_key
}

payload = {
    'identifier': config.username,
    'password': config.password
}

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
    url = BASEURL + "/session"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    cst = r.headers['cst']
    xsecuritytoken = r.headers['x-security-token']
    fullheaders = {
        'content-type': 'application/json; charset=UTF-8',
        'Accept': 'application/json; charset=UTF-8',
        'X-IG-API-KEY': config.api_key,
        'CST': cst,
        'X-SECURITY-TOKEN': xsecuritytoken
    }

    body = r.json()
    lightstreamerEndpoint = body[u'lightstreamerEndpoint']
    clientId = body[u'clientId']
    accounts = body[u'accounts']

    # Depending on how many accounts you have with IG the '0' may need to change to select the correct one (spread bet, CFD account etc)
    accountId = accounts[0][u'accountId']

    client = igls.LsClient(lightstreamerEndpoint+"/lightstreamer/")
    client.on_state.listen(on_state)
    client.create_session(username=accountId, password='CST-'+cst+'|XST-'+xsecuritytoken, adapter_set='')

    for item_id in ['L1:CS.D.GBPUSD.CFD.IP', 'L1:CS.D.USDJPY.CFD.IP']:
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
