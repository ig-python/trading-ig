.. image:: https://img.shields.io/pypi/v/trading-ig.svg
    :target: https://pypi.python.org/pypi/trading-ig/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/trading-ig.svg
    :target: https://pypi.python.org/pypi/trading-ig/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/wheel/trading-ig.svg
    :target: https://pypi.python.org/pypi/trading-ig/
    :alt: Wheel format

.. image:: https://img.shields.io/pypi/l/trading-ig.svg
    :target: https://pypi.python.org/pypi/trading-ig/
    :alt: License

.. image:: https://img.shields.io/pypi/status/trading-ig.svg
    :target: https://pypi.python.org/pypi/trading-ig/
    :alt: Development Status

.. image:: https://img.shields.io/pypi/dm/trading-ig.svg
    :target: https://pypi.python.org/pypi/trading-ig/
    :alt: Downloads monthly

.. image:: https://readthedocs.org/projects/trading-ig/badge/?version=latest
    :target: https://trading-ig.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/ig-python/trading-ig/badge.svg
    :target: https://coveralls.io/github/ig-python/trading-ig
    :alt: Test Coverage

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

trading-ig
==========

A lightweight Python wrapper for the IG Markets API. Simplifies access to the IG REST and Streaming APIs.

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

A number of dependencies in this project are marked as 'optional', this is *by design*. There is a brief
explanation in `this FAQ item <https://trading-ig.readthedocs.io/en/latest/faq.html#optional-dependencies>`_.

For full details, see `pyproject.toml <https://github.com/ig-python/trading-ig/blob/master/pyproject.toml>`_

Installation
------------

This project uses `Poetry <https://python-poetry.org/>`_.

Adding to an existing Poetry project::

    $ poetry add trading-ig

With all the optional dependencies::

    $ poetry add trading-ig[pandas,munch,tenacity]

Cloning the project with Poetry::

    $ git clone https://github.com/ig-python/trading-ig
    $ cd trading-ig
    $ poetry install

And with all optional dependencies::

    $ poetry install --extras "pandas munch tenacity"

Installing with pip::

    $ pip install trading-ig

And with all optional dependencies::

    $ pip install trading-ig pandas munch tenacity

What if I need help?
--------------------

This library is maintained by one busy developer in his spare time, with very little time for support.

If you have a problem using this library, the first thing to do is to try to isolate where the problem is. The IG platform is a complex application, and there are many ways to make mistakes using it. Just because you see an error, it does not necessarily mean there is a problem with this library. If you encounter an issue, you should follow these steps, in order:

1. Check if there a problem with the IG platform. From time to time the IG platform itself has issues, especially the DEMO environment. If you see a message like `ConnectionRefusedError`, or a 500 Server error, then it could be an issue with the IG platform. IG provide a `status page <https://status.ig.com/>`_, though its accuracy is questionable. You can also check the `IG Community forums <https://community.ig.com/>`__. If there are platform issues, its likely someone will have already posted a message there.

2. Check if there is a problem with your code. Most of the API endpoints have multiple options, multiple versions, multiple ways of accessing them, and multiple interdependent parameters. Incoming data is validated on the server, and problems will be reported back in the response. You should

    * check the documentation (`REST <https://labs.ig.com/rest-trading-api-reference>`__, `Streaming <https://labs.ig.com/streaming-api-reference>`__) to make sure you are calling the APIs correctly
    * look at the `sample code <https://github.com/ig-python/trading-ig/tree/master/sample>`_ and `unit and integration tests <https://github.com/ig-python/trading-ig/tree/master/tests>`_. There are example snippets for most API endpoints.
    * repeat the API call using the IG companion tools (`REST <https://labs.ig.com/sample-apps/api-companion/index.html>`__, `Streaming <https://labs.ig.com/sample-apps/streaming-companion/index.html>`__). If you get the same result, then it is likely that you are using the API incorrectly.

    In this case you should:

    * read the IG docs more carefully, or
    * post a question in the `IG Community site <https://community.ig.com/>`__, or
    * contact the `API support team <mailto:webapisupport@ig.com>`_

3. If you're sure that the problem is with this library, please:

    * provide *everything* necessary to reproduce the problem
    * include the full script that produces the error, including import statements
    * ideally this should be a *minimal example* - the shortest possible script that reproduces the problem
    * dependencies and their versions
    * the full output trace including the error messages

    An issue without all this information may be ignored and/or closed without response

Docs
----

`<https://trading-ig.readthedocs.io/>`_

License
-------

BSD (See `LICENSE <https://github.com/ig-python/trading-ig/blob/master/LICENSE>`_)

