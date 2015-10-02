IG Markets STREAM API - Python Library
======================================

You can use the IG Markets STREAM API to get realtime price, balance...

Full details about the API along with information about how to open an
account with IG can be found at the link below:

http://labs.ig.com/

How To Use The Library
----------------------

Run sample using:

::

    $ python sample/stream_ig.py
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
