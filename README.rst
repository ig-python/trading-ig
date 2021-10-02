.. image:: https://img.shields.io/pypi/v/trading_ig.svg
    :target: https://pypi.python.org/pypi/trading_ig/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/trading_ig.svg
    :target: https://pypi.python.org/pypi/trading_ig/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/wheel/trading_ig.svg
    :target: https://pypi.python.org/pypi/trading_ig/
    :alt: Wheel format

.. image:: https://img.shields.io/pypi/l/trading_ig.svg
    :target: https://pypi.python.org/pypi/trading_ig/
    :alt: License

.. image:: https://img.shields.io/pypi/status/trading_ig.svg
    :target: https://pypi.python.org/pypi/trading_ig/
    :alt: Development Status

.. image:: https://img.shields.io/pypi/dm/trading_ig.svg
    :target: https://pypi.python.org/pypi/trading_ig/
    :alt: Downloads monthly

.. image:: https://requires.io/github/ig-python/ig-markets-api-python-library/requirements.svg?branch=master
    :target: https://requires.io/github/ig-python/ig-markets-api-python-library/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://readthedocs.org/projects/trading-ig/badge/?version=latest
    :target: https://trading-ig.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/ig-python/ig-markets-api-python-library/badge.svg
    :target: https://coveralls.io/github/ig-python/ig-markets-api-python-library
    :alt: Test Coverage

trading_ig
==========

A lightweight Python wrapper for the IG Markets API. Simplifies access to the IG REST and Streaming APIs
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

From `Python package index <https://pypi.org/project/trading_ig/>`_::

    $ pip install trading_ig

with `Poetry <https://python-poetry.org/>`_::

    $ git clone https://github.com/ig-python/ig-markets-api-python-library
    $ cd ig-markets-api-python-library
    $ poetry install

or with optional packages::

    $ poetry install --extras "pandas munch"

From source::

    $ git clone https://github.com/ig-python/ig-markets-api-python-library
    $ cd ig-markets-api-python-library
    $ python setup.py install

or direct from Github::

    $ pip install git+https://github.com/ig-python/ig-markets-api-python-library

Dependencies
------------

* `requests <https://pypi.org/project/requests/>`_
* `pycryptodome <https://pypi.org/project/pycryptodome/>`_

For full details, see `pyproject.toml <https://github.com/ig-python/ig-markets-api-python-library/blob/master/pyproject.toml>`_

Docs
----

`<https://trading_ig.readthedocs.io/>`_

License
-------

BSD (See `LICENSE <https://github.com/ig-python/ig-markets-api-python-library/blob/master/LICENSE>`_)

