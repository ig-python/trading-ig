import logging
from queue import Queue
from threading import Thread
import time

from lightstreamer.client import SubscriptionListener, ItemUpdate

from trading_ig import IGStreamService
from .ticker import Ticker
from .ticker import TickerSubscription

logger = logging.getLogger(__name__)


class StreamingManager:
    def __init__(self, service: IGStreamService):
        self._service = service
        self._subs = {}

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

    def start_tick_subscription(self, epic) -> TickerSubscription:
        tick_sub = TickerSubscription(epic)
        tick_sub.addListener(TickerListener(self._queue))
        self.service.subscribe(tick_sub)
        self._subs[epic] = tick_sub
        return tick_sub

    def stop_tick_subscription(self, epic):
        subscription = self._subs.pop(epic)
        self.service.unsubscribe(subscription)

    def ticker(self, epic, timeout_length=3):
        # we won't have a ticker until at least one update is received from server,
        # let's give it a few seconds
        timeout = time.time() + timeout_length
        while True:
            logger.info(f"Waiting for ticker for '{epic}'...")
            if epic in self._tickers or time.time() > timeout:
                break
            time.sleep(0.25)
        try:
            ticker = self._tickers[epic]
        except KeyError:
            raise Exception(
                f"No ticker found for {epic} after "
                f"waiting {timeout_length} seconds - giving up"
            )
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


class TickerListener(SubscriptionListener):
    def __init__(self, queue: Queue) -> None:
        self._queue = queue

    def onItemUpdate(self, update: ItemUpdate):
        self._queue.put(update)

    def onSubscription(self):
        logger.info("TickerListener onSubscription()")

    def onSubscriptionError(self, code, message):
        logger.info(f"TickerListener onSubscriptionError(): '{code}' {message}")

    def onUnsubscription(self):
        logger.info("TickerListener onUnsubscription()")


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
            name = item.getItemName()
            if name.startswith("CHART:"):
                self._handle_ticker_update(item)

            logger.debug(f"Consumer thread alive. queue length: {self._queue.qsize()}")

    def _handle_ticker_update(self, item: ItemUpdate):
        epic = Ticker.identifier(item.getItemName())

        if epic not in self.manager.tickers:
            ticker = Ticker(epic)
            self.manager.tickers[epic] = ticker

        ticker = self.manager.tickers[epic]
        ticker.populate(item.getChangedFields())
