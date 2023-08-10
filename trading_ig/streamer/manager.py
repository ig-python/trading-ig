import logging
from queue import Queue
from threading import Thread
import time

from trading_ig import IGStreamService
from .ticker import Ticker
from .ticker import TickerSubscription

logger = logging.getLogger(__name__)


class StreamingManager:
    def __init__(self, service: IGStreamService):
        self._service = service
        self._sub_keys = {}

        # setup data objects
        self._tickers = {}

        # set up consumer queue
        self._queue = Queue()
        self._consumer_thread = Consumer(self._queue, self)
        self._consumer_thread.start()

    @property
    def service(self):
        return self._service

    @property
    def tickers(self):
        return self._tickers

    def start_tick_subscription(self, epic) -> int:
        tick_sub = TickerSubscription(epic)
        tick_sub.addlistener(self.on_update)
        sub_key = self.service.ls_client.subscribe(tick_sub)
        self._sub_keys[epic] = sub_key
        return sub_key

    def stop_tick_subscription(self, epic):
        sub_key = self._sub_keys.pop(epic)
        self.service.ls_client.unsubscribe(sub_key)

    def ticker(self, epic):
        # we won't have a ticker until at least one update is received from server,
        # let's give it a few seconds
        timeout = time.time() + 3
        while True:
            logger.debug("Waiting for ticker...")
            if epic in self._tickers or time.time() > timeout:
                break
            time.sleep(0.25)
        ticker = self._tickers[epic]
        if not ticker:
            raise Exception(f"No ticker found for {epic}, giving up")
        return ticker

    def on_update(self, update):
        self._queue.put(update)

    def stop_subscriptions(self):
        logger.info("Unsubscribing from all")
        self.service.unsubscribe_all()
        self.service.disconnect()
        if self._consumer_thread:
            self._consumer_thread.join(timeout=5)
            self._consumer_thread = None


class Consumer(Thread):
    def __init__(self, queue: Queue, manager: StreamingManager):
        super().__init__(name="ConsumerThread", daemon=True)
        self._queue = queue
        self._manager = manager

    @property
    def manager(self):
        return self._manager

    def run(self):
        logger.info("Consumer: Running")
        while True:
            item = self._queue.get()

            # deal with each different type of update
            name = item["name"]
            if name.startswith("CHART:"):
                self._handle_ticker_update(item)

            logger.debug(
                f"Consumer thread alive. queue length: {self._queue.qsize()}"
            )

    def _handle_ticker_update(self, item):
        epic = Ticker.identifier(item["name"])

        if epic not in self.manager.tickers:
            ticker = Ticker(epic)
            self.manager.tickers[epic] = ticker

        ticker = self.manager.tickers[epic]
        ticker.populate(item["values"])
