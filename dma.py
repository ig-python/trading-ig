import xlwings as xw

from trading_ig import IGService
import logging

from datetime import timedelta
import requests_cache

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

username = "DEMO-<USERNAME>"
password = ""
api_key = ""
acc_type = "DEMO" # LIVE / DEMO
acc_number = ""
ig_service = 0

@xw.func
def create_session():
    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(cache_name='cache', backend='sqlite', expire_after=expire_after)
    # set expire_after=None if you don't want cache expiration
    # set expire_after=0 if you don't want to cache queries 
    #config = IGServiceConfig()

    # no cache
    global ig_service
    ig_service = IGService(username, password, api_key, acc_type)

    # if you want to globally cache queries
    #ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)

@xw.func
def create_dma_equity_working_order(direction, epic, level, size, time_in_force,  order_type, limit_distance=None, stop_distance=None):
    logging.basicConfig(level=logging.DEBUG)
    
    global ig_service
    ig_service.create_session()

    #("BUY","UA.D.AMZN.CASH.IP","1600","9","GoodForDay","MarketLimit")
    deal_reference = ig_service.create_dma_equity_working_order(direction, epic, level, size, time_in_force,  order_type, limit_distance, stop_distance)
    #ig_service.delete_working_order("abc")
    #return "abc"
    return deal_reference

    