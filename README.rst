
IG Markets API - Python Library
===============================

This is a fork from `ig-markets-api-python-library <https://github.com/ig-python/ig-markets-api-python-library>`_

Added support for ``asyncio`` and ``aiohttp``

Usage
--------

.. code:: python

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    params = IGParams()
    params.Url = os.environ['IG_URL']
    params.Key = os.environ['X_IG_API_KEY']
    params.Identifier = os.environ['IDENTIFIER']
    params.Password = os.environ['PASSWORD']


    async with IGClient(params, logger) as client:
        auth = await client.Login()
        print(auth)

        order = Order() # populate epic etc.
        deal = await client.CreatePosition(order)
        print(deal)

        await client.Logout()

More
----

Full details about the API along with information about how to open an account with IG can be found at the link below:

http://labs.ig.com/


Install
-------

From Python package index
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ pip install pyIG


Thanks to
---------
-  `ig-markets-api-python-library <https://github.com/ig-python/ig-markets-api-python-library>`_

