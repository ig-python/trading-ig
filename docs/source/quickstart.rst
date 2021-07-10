Quickstart
==================

Installation
------------

From `Python package index <https://pypi.org/project/trading_ig/>`_::

    $ pip install trading_ig

with `Poetry <https://python-poetry.org/>`_::

    $ git clone https://github.com/ig-python/ig-markets-api-python-library
    $ cd ig-markets-api-python-library
    $ poetry install

or with optional packages::

    $ poetry install --extras "pandas munch tenacity"

From source::

    $ git clone https://github.com/ig-python/ig-markets-api-python-library
    $ cd ig-markets-api-python-library
    $ python setup.py install

or direct from Github::

    $ pip install git+https://github.com/ig-python/ig-markets-api-python-library


Configuration
-------------

Config file
^^^^^^^^^^^

Make a copy of the config template module (``trading_ig_config.default.py``), and rename
``trading_ig_config.py``. Edit the new file, replacing the variables with your own::

    class config(object):
        username = "your_username"
        password = "your_password"
        api_key = "your_api_key"
        acc_type = "DEMO"
        acc_number = "your_account_number"


Environment variables
^^^^^^^^^^^^^^^^^^^^^

If any exceptions are raised loading the config, IGService will attempt to find your authentication details from
environment variables

::

    $ export IG_SERVICE_USERNAME="your_username"
    $ export IG_SERVICE_PASSWORD="your_password"
    $ export IG_SERVICE_API_KEY="your_api_key"
    $ export IG_SERVICE_ACC_NUMBER="your_account_number"


Connection
----------

>>> from trading_ig.rest import IGService
>>> from trading_ig.config import config
>>> ig_service = IGService(config.username, config.password, config.api_key)
>>> ig = ig_service.create_session()
>>> ig


Using the REST API
------------------

Searching for a market

>>> results = ig_service.search_markets("gold")
>>> results


Get info about a market

>>> market = ig_service.fetch_market_by_epic('CS.D.USCGC.TODAY.IP')
>>> market


Getting historic prices

>>> result = ig_service.fetch_historical_prices_by_epic(epic='CS.D.USCGC.TODAY.IP')
>>> result['prices']

Opening a position

>>> resp = ig_service.create_open_position(
        currency_code='GBP',
        direction='BUY',
        epic='CS.D.USCGC.TODAY.IP',
        order_type='MARKET',
        expiry='DFB',
        force_open='false',
        guaranteed_stop='false',
        size=0.5, level=None,
        limit_distance=None,
        limit_level=None,
        quote_id=None,
        stop_level=None,
        stop_distance=None,
        trailing_stop=None,
        trailing_stop_increment=None)
>>> resp

Getting account activity

>>> from_date = datetime(2021, 1, 1)
>>> activities = ig_service.fetch_account_activity(from_date=from_date)
>>> activities


Using the Streaming API
-----------------------

Assuming config as above

>>> from trading_ig import IGService, IGStreamService
>>> from trading_ig.config import config
>>> from trading_ig.lightstreamer import Subscription

>>> def on_update(item):
>>>     print("{UPDATE_TIME:<8} {stock_name:<19} Bid {BID:>5} Ask {OFFER:>5}".format(stock_name=item["name"], **item["values"]))

>>> ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, acc_number=config.acc_number)
>>> ig_stream_service = IGStreamService(ig_service)
>>> ig_stream_service.create_session()
>>> sub = Subscription(mode="MERGE", items=["L1:CS.D.GBPUSD.TODAY.IP"], fields=["UPDATE_TIME", "BID", "OFFER"])
>>> sub.addlistener(on_update)
>>> ig_stream_service.ls_client.subscribe(sub)
>>> ig_stream_service.disconnect()