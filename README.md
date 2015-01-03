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

with `trading_ig_config.py`

```python
class config(object):
    username = "YOUR_USERNAME"
    password = "YOUR_PASSWORD"
    api_key = "YOUR_API_KEY"
    acc_type = "DEMO" # LIVE / DEMO
    acc_number = "ABC123"
```


HTTP REST API
-------------
If you need to submit trade orders, open positions, close positions and view market sentiment,
see https://github.com/femtotrader/ig-markets-rest-api-python-library


Work in progress
----------------
see http://labs.ig.com/node/98 and https://labs.ig.com/node/28

Thanks to
---------
 - ixta
 - Chris
 - colombao
 - gianluca.finocchiaro
