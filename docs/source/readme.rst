trading_ig
==========

A lightweight wrapper for the IG Markets API written in Python. Simplifies access to the IG REST and streaming APIs
with a live or demo account.

What is it?
-----------

`IG Markets <https://www.ig.com/>`_ provides financial spread betting and CFD platforms for trading equities, forex,
commodities, indices, cryptocurrencies, bonds, rates, options and more.

IG provide APIs so that developers can access their platforms programmatically. Using the APIs you can
get live and historical data, automate your trades, or create apps. For details about the IG APIs please see their site:

https://labs.ig.com/

NOTE: this is not an IG project. Use it at your own risk

Installation
------------

From `Python package index <https://pypi.org/project/trading_ig/>`_

::

    $ pip install trading_ig

From source

::

    $ git clone https://github.com/ig-python/ig-markets-api-python-library
    $ cd ig-markets-api-python-library
    $ python setup.py install

or

::

    $ pip install git+https://github.com/ig-python/ig-markets-api-python-library

Dependencies
------------

* `requests <https://pypi.org/project/requests/>`_
* `pycryptodome <https://pypi.org/project/pycryptodome/>`_
* `pandas 1.0.5 <https://pypi.org/project/pandas/1.0.5/>`_

For full details, see `requirements.txt <https://github.com/ig-python/ig-markets-api-python-library/blob/master/requirements.txt>`_

Docs
----

`<https://trading_ig.readthedocs.io/en/>`_

License
-------

BSD (See `LICENSE <https://github.com/ig-python/ig-markets-api-python-library/blob/master/LICENSE>`_)