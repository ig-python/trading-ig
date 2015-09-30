[![Requirements Status](https://requires.io/github/femtotrader/ig-markets-stream-api-python-library/requirements.svg?branch=master)](https://requires.io/github/femtotrader/ig-markets-stream-api-python-library/requirements/?branch=master)
[![Code Health](https://landscape.io/github/femtotrader/ig-markets-stream-api-python-library/master/landscape.svg?style=flat)](https://landscape.io/github/femtotrader/ig-markets-stream-api-python-library/master)

ig-markets-stream-api-python-library
====================================

A lightweight Python library that can be used to get live data from IG Markets STREAM API with a LIVE or DEMO account

You can use the IG Markets STREAM API to get realtime price, balance...

IG Markets provide Retail Spread Betting and CFD accounts for trading Equities, Forex, Commodities, Indices and much more.

Full details about the API along with information about how to open an account with IG can be found at the link below:

http://labs.ig.com/

How To Use The Library
----------------------

Using this library to connect to the IG Markets API is extremely easy.

Copy `trading_ig_config_default.py` to `trading_ig_config.py` and update it

```python
class config(object):
    username = "YOUR_USERNAME"
    password = "YOUR_PASSWORD"
    api_key = "YOUR_API_KEY"
    acc_type = "DEMO" # LIVE / DEMO
    acc_number = "ABC123"
```

Run sample using:


    $ python2 sample/main.py
    ('New state:', 'connecting Lightstreamer session')
    ('New state:', 'connected Lightstreamer session')
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:27', u'119.753', u'119.761', u'0.020', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:27', u'119.752', u'119.760', u'0.019', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:28', u'119.749', u'119.757', u'0.016', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:28', u'119.750', u'119.758', u'0.017', u'TRADEABLE']
    price update for L1:CS.D.GBPUSD.CFD.IP= [u'16:31:28', u'1.51190', u'1.51200', u'-0.00302', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:28', u'119.749', u'119.757', u'0.016', u'TRADEABLE']
    price update for L1:CS.D.GBPUSD.CFD.IP= [u'16:31:28', u'1.51189', u'1.51199', u'-0.00303', u'TRADEABLE']
    price update for L1:CS.D.GBPUSD.CFD.IP= [u'16:31:28', u'1.51188', u'1.51198', u'-0.00304', u'TRADEABLE']
    price update for L1:CS.D.GBPUSD.CFD.IP= [u'16:31:29', u'1.51189', u'1.51199', u'-0.00303', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:30', u'119.750', u'119.758', u'0.017', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:30', u'119.747', u'119.762', u'0.017', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:30', u'119.752', u'119.760', u'0.019', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:30', u'119.753', u'119.761', u'0.020', u'TRADEABLE']
    price update for L1:CS.D.GBPUSD.CFD.IP= [u'16:31:31', u'1.51188', u'1.51198', u'-0.00304', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:31', u'119.754', u'119.762', u'0.021', u'TRADEABLE']
    price update for L1:CS.D.USDJPY.CFD.IP= [u'16:31:31', u'119.755', u'119.763', u'0.022', u'TRADEABLE']


HTTP REST API
-------------
If you need to submit trade orders, open positions, close positions and view market sentiment,
see https://github.com/femtotrader/ig-markets-rest-api-python-library


Work in progress
----------------
see :

 - http://labs.ig.com/node/98
 - https://labs.ig.com/node/28
 - http://www.andlil.com/forum/script-api-ig-stream-rest-t10091-10.html

Thanks to
---------
 - ixta
 - Chris
 - colombao
 - gianluca.finocchiaro