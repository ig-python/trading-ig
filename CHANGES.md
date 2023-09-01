# Release notes

## 0.0.21 (2023-09-01)
* Black entire codebase
* Black added to CI pipeline
* flake8 entire codebase
* using official Lightstreamer client SDK
* fixed a bug in fetch_activity() where bet size was not included
* 'forceOpen' defaults to False in create_working_order()
* logging improvements

## 0.0.20 (2023-01-25)
* repo name changed to 'trading-ig'

## 0.0.19 (2023-01-05)
* fix for 'ValueError: columns cannot be a set' error with pandas 1.5.2+ (PR#267)
* fetch_historical_prices*() methods improvements (Issue #272)
* remove requirements status badge (Issue #259)
* publish with API token (Issue #260)
* specify importlib-metadata version to prevent flake8 problems with python 3.7
* updating github actions to latest versions

## 0.0.18 (2022-08-23)
* better fix for http error 405 when confirming deal (PR#256)
* fix use of forceOpen param when opening a new position (PR#250)

## 0.0.17 (2022-01-26)
* added an optional rate limiter, with leaky bucket algo (PR#243)

## 0.0.16 (2022-01-01)
* fix for http error 405 response from IG when confirming deal (PR#237)
* updating Poetry for automated testing
* removing some unused legacy project config
* removing support for unsupported Python 3.6, adding 3.10
* better handling and docs for optional dependencies (#216, #240)
* fixing occasional KeyError when deleting session headers (#238)

## 0.0.15 (2021-10-19)
* optional dependency `tenacity` updated to latest
* documentation improvements
* 
## 0.0.14 (2021-10-04)
* fixes the bug where guaranteed stop loss was replaced with a normal stop loss on working order update (#224)
* legacy 'setup.py' style project config files removed

## 0.0.13 (2021-10-02)
* switch accounts bug fixed (#220)
* coverage badge and report added
* Sphinx is now a development dependency (#228)
* test improvements

## 0.0.12 (2021-07-28)
* uses Poetry to publish to [Python Package Index](https://pypi.org/)

## 0.0.11 (2021-07-19)
* code samples improved, new FAQ
* Adds support for update open position v2
* new function to calculate mid prices for historic data
* Adds support for getting and updating account prefs
* Adds support for `/markets` endpoint for getting details of multiple markets 
* new sample script to traverse navigation tree and get epics, new FAQ

## 0.0.10 (2021-07-10)

* simplified request headers: `requests.Session` now handles persistence
* adds support for v3 session creation (#157)
* implementation and test for fetch_working_orders() v2 (like PR#187)
* adds support for fetch_historical_prices_by_epic_and_date_range() v2 
* adds support for fetch_open_positions() v2
* dependency management with [Python Poetry](https://python-poetry.org/) (#149)
* more robust handling of IG API rate limits
* support for all the `/history/activity` endpoints
* better test coverage. now 80% for `rest.py` (#38)
* documentation improvements

## 0.0.9 (2021-03-19)

* integration and unit tests improved
* remove reference to adapter (#190)
* pandas 1.2.0 (#184)
* paged historical data can be captured with one request (#183)
* paging fixed for historical data (#175)
* error fixed when closing stream (#174)

## 0.0.8

* docs restructured and reintegrated with readthedocs.io
* Fix for a bug in 'expand-columns()' that would cause an error if values were missing/null
* unit tests for v3 historic prices method
* Tidy up usage of "version" across the REST API to make it consistent
* Marked methods that use an outdated version with TODOs
* Fixed issues with switch_account(), delete_working_order() etc. which were not specifying a version correctly
* unit tests for v1, v2 historic prices methods
* allowing historic prices format to be defined at runtime
* new optional flatter format for historic prices
* release notes

## 0.0.7

* CI build fixed
* scheduled integration test added
* initial unit tests created for login, utils
* historical prices methods fixed to use NaN instead of None
* requirements defined explicitly
* fixing flake8 errors
* fixed stream_connection bug
* fixed encrypted password bug
* fixed streaming LOOP problem
* fixed various API version issues
* fixed missing Crypto dependency issue
* fixed Pandas version dependency issue
* support removed for older python versions
* formatting with black
* fixing date format issues
* Fetch multiple client sentiment markets
* PEP8 improvements
* Improve not-found handling on working order creation
* Break out of accounts loop when a user is found
* rest: create_working_order upgrade to v2 api
* Add fetch transaction history v2 api
* Add systemd watchdog support to the lightstreamer library
* Add method to GET current session details
* historical prices v3
* better exception handling
* Update lightstreamer library


## 0.0.6

* initial / undocumented
