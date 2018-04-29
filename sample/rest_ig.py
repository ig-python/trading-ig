#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
IG Markets REST API sample with Python
2015 FemtoTrader
"""

from trading_ig import IGService
from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache


def main():
    logging.basicConfig(level=logging.DEBUG)

    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(
        cache_name='cache', backend='sqlite', expire_after=expire_after
    )
    # set expire_after=None if you don't want cache expiration
    # set expire_after=0 if you don't want to cache queries

    #config = IGServiceConfig()

    # no cache
    ig_service = IGService(
        config.username, config.password, config.api_key, config.acc_type
    )

    # if you want to globally cache queries
    #ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)

    ig_service.create_session()

    accounts = ig_service.fetch_accounts()
    print("accounts:\n%s" % accounts)

    #account_info = ig_service.switch_account(config.acc_number, False)
    # print(account_info)

    #open_positions = ig_service.fetch_open_positions()
    #print("open_positions:\n%s" % open_positions)

    print("")

    #working_orders = ig_service.fetch_working_orders()
    #print("working_orders:\n%s" % working_orders)

    print("")

    #epic = 'CS.D.EURUSD.MINI.IP'
    epic = 'IX.D.ASX.IFM.IP'  # US (SPY) - mini

    resolution = 'D'
    # see from pandas.tseries.frequencies import to_offset
    #resolution = 'H'
    #resolution = '1Min'

    num_points = 10
    response = ig_service.fetch_historical_prices_by_epic_and_num_points(
        epic, resolution, num_points
    )
    # Exception: error.public-api.exceeded-account-historical-data-allowance

    # if you want to cache this query
    #response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points, session)

    #df_ask = response['prices']['ask']
    #print("ask prices:\n%s" % df_ask)

    #(start_date, end_date) = ('2015-09-15', '2015-09-28')
    #response = ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date)

    # if you want to cache this query
    #response = ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date, session)
    #df_ask = response['prices']['ask']
    #print("ask prices:\n%s" % df_ask)


if __name__ == '__main__':
    main()
