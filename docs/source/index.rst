trading_ig
==========

A lightweight wrapper for the IG Markets API written in Python. Simplifies access to the IG REST and Streaming APIs
with a live or demo account.

What is it?
-----------

`IG Markets <https://www.ig.com/>`_ provides financial spread betting and CFD platforms for trading equities, forex,
commodities, indices, cryptocurrencies, bonds, rates, options and more.

IG provide APIs so that developers can access their platforms programmatically. Using the APIs you can
get live and historical data, automate your trades, or create apps. For details about the IG APIs please see their site:

https://labs.ig.com/

NOTE: this is not an IG project. Use it at your own risk


Dependencies
------------

* `requests <https://pypi.org/project/requests/>`_
* `pycryptodome <https://pypi.org/project/pycryptodome/>`_

For full details, see `pyproject.toml <https://github.com/ig-python/ig-markets-api-python-library/blob/master/pyproject.toml>`_

Support
------------
This is an open source project, maintained by busy volunteers in their spare time. It should make it easier and
quicker for you to use the IG APIs. However, it is not a support resource for users of the IG APIs. IG have their
own support site:

https://community.ig.com/

If you have a problem when using this library, please think carefully about the likely cause. If it is:

* a bug in this library
* a request for a feature
* missing or confusing documentation

then please create an `issue <https://github.com/ig-python/ig-markets-api-python-library/issues>`_. See the guidance
notes :ref:`here <report_problem>`.

For anything else, please use the documentation and tools provided by IG

* `Getting Started Guide <https://labs.ig.com/gettingstarted>`_
* `REST API Guide <https://labs.ig.com/rest-trading-api-guide>`_
* `REST API Reference <https://labs.ig.com/rest-trading-api-reference>`_
* `REST API Companion <https://labs.ig.com/sample-apps/api-companion/index.html>`_
* `Streaming API Guide <https://labs.ig.com/streaming-api-guide>`_
* `Streaming API Reference <https://labs.ig.com/streaming-api-reference>`_
* `Streaming API Companion <https://labs.ig.com/sample-apps/streaming-companion/index.html>`_


Contributing
------------

Contributions are welcome. We use some automated linting and testing so please make your code passes the tests, see
:ref:`here <running_tests>`


License
-------

BSD (See `LICENSE <https://github.com/ig-python/ig-markets-api-python-library/blob/master/LICENSE>`_)

See also
--------

.. toctree::
   :maxdepth: 2

   quickstart.rst
   faq.rst
   rest.rst
   stream.rst

Credits
-------

Created by Femto Trader, Lewis Barber, Sudipta Basak

Maintained by Andy Geach
