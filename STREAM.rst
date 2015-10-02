|Requirements Status| |Code Health|

ig-markets-stream-api-python-library
====================================

A lightweight Python library that can be used to get live data from IG
Markets STREAM API with a LIVE or DEMO account

You can use the IG Markets STREAM API to get realtime price, balance...

IG Markets provide Retail Spread Betting and CFD accounts for trading
Equities, Forex, Commodities, Indices and much more.

Full details about the API along with information about how to open an
account with IG can be found at the link below:

http://labs.ig.com/

How To Use The Library
----------------------

Using this library to connect to the IG Markets API is extremely easy.

Copy ``trading_ig_config_default.py`` to ``trading_ig_config.py`` and
update it

.. code:: python

    class config(object):
        username = "YOUR_USERNAME"
        password = "YOUR_PASSWORD"
        api_key = "YOUR_API_KEY"
        acc_type = "DEMO" # LIVE / DEMO
        acc_number = "ABC123"

Run sample using:

::

    $ python sample/main.py
    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): demo-api.ig.com
    INFO:ig_stream:Starting connection with https://demo-apd.marketdatasystems.com
    L1:CS.D.USDJPY.CFD.IP: Time 20:35:43 - Bid 119.870 - Ask 119.885
    L1:CS.D.GBPUSD.CFD.IP: Time 20:35:46 - Bid 1.51270 - Ask 1.51290
    ----------HIT CR TO UNSUBSCRIBE AND DISCONNECT FROM     LIGHTSTREAMER-----------
    L1:CS.D.USDJPY.CFD.IP: Time 20:35:43 - Bid 119.870 - Ask 119.885
    L1:CS.D.USDJPY.CFD.IP: Time 20:35:48 - Bid 119.871 - Ask 119.886
    L1:CS.D.GBPUSD.CFD.IP: Time 20:35:48 - Bid 1.51271 - Ask 1.51291
    L1:CS.D.USDJPY.CFD.IP: Time 20:35:48 - Bid 119.870 - Ask 119.885
    L1:CS.D.GBPUSD.CFD.IP: Time 20:35:49 - Bid 1.51270 - Ask 1.51290

    INFO:lightstreamer:Unsubscribed successfully
    WARNING:lightstreamer:Server error
    DISCONNECTED FROM LIGHTSTREAMER

HTTP REST API
-------------

If you need to submit trade orders, open positions, close positions and
view market sentiment, see
https://github.com/femtotrader/ig-markets-rest-api-python-library

Work in progress
----------------

see :

-  http://labs.ig.com/node/98
-  https://labs.ig.com/node/28
-  http://www.andlil.com/forum/script-api-ig-stream-rest-t10091-10.html

Thanks to
---------

-  ixta
-  Chris
-  colombao
-  gianluca.finocchiaro

.. |Requirements Status| image:: https://requires.io/github/femtotrader/ig-markets-stream-api-python-library/requirements.svg?branch=master
   :target: https://requires.io/github/femtotrader/ig-markets-stream-api-python-library/requirements/?branch=master
.. |Code Health| image:: https://landscape.io/github/femtotrader/ig-markets-stream-api-python-library/master/landscape.svg?style=flat
   :target: https://landscape.io/github/femtotrader/ig-markets-stream-api-python-library/master
