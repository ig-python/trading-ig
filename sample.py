#!/usr/bin/env python
#-*- coding:utf-8 -*-

# IG API Trader

import igls,requests,json, time
from ig_service_config import *

if acc_type.upper() == "DEMO":
    sessionurl = 'https://demo-api.ig.com/gateway/deal/session'
elif acc_type.upper() == "LIVE":
    sessionurl = 'https://api.ig.com/gateway/deal/session'
else:
    raise(NotImplementedError("acc_type is %r but it should be either 'DEMO' or 'LIVE'" % acc_type))

headers = {'content-type': 'application/json; charset=UTF-8', 'Accept': 'application/json; charset=UTF-8', 'X-IG-API-KEY': api_key}
payload = {'identifier': username, 'password': password}

# Tell the user when the Lighstreamer connection state changes
def on_state(state):
    print 'New state:', state
    igls.LOG.debug('New state: '+str(state))

# Process a lighstreamer price update
def processPriceUpdate(item, myUpdateField):
    print "price update = "+str(myUpdateField)

# Process an update of the users trading account balance
def processBalanceUpdate(item, myUpdateField):
    print "balance update = "+str(myUpdateField)


if __name__ == '__main__':
       
    r = requests.post(sessionurl, data=json.dumps(payload), headers=headers, verify=False)

    cst = r.headers['cst']
    xsecuritytoken = r.headers['x-security-token']
    fullheaders = {'content-type': 'application/json; charset=UTF-8', 'Accept': 'application/json; charset=UTF-8', 'X-IG-API-KEY': api_key, 'CST': cst, 'X-SECURITY-TOKEN': xsecuritytoken }

    body = r.json()
    lightstreamerEndpoint = body[u'lightstreamerEndpoint']
    clientId = body[u'clientId']
    accounts = body[u'accounts']

    # Depending on how many accounts you have with IG the '0' may need to change to select the correct one (spread bet, CFD account etc)
    accountId = accounts[0][u'accountId']
    
    client = igls.LsClient(lightstreamerEndpoint+"/lightstreamer/")
    client.on_state.listen(on_state)
    client.create_session(username=accountId, password='CST-'+cst+'|XST-'+xsecuritytoken, adapter_set='')

    priceTable = igls.Table(client,
        mode=igls.MODE_MERGE,
        item_ids='L1:CS.D.GBPUSD.CFD.IP',
        schema='UPDATE_TIME BID OFFER CHANGE MARKET_STATE',
        item_factory=lambda row: tuple(float(v) for v in row)
    )

    priceTable.on_update.listen(processPriceUpdate)

    balanceTable = igls.Table(client,
        mode=igls.MODE_MERGE,
        item_ids='ACCOUNT:'+accountId,
        schema='AVAILABLE_CASH',
        item_factory=lambda row: tuple(string(v) for v in row))

    balanceTable.on_update.listen(processBalanceUpdate)


    while True:
        time.sleep(10)
        