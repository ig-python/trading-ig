#!/usr/bin/python

#  Copyright 2015 Weswit s.r.l.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
import traceback
import logging
from trading_ig.lightstreamer import LSClient, Subscription


# A simple function acting as a Subscription listener
def on_item_update(item_update):
    print("{stock_name:<19}: Last{last_price:>6} - Time {time:<8} - "
          "Bid {bid:>5} - Ask {ask:>5}".format(**item_update["values"]))


def main():
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    # Establishing a new connection to Lightstreamer Server
    print("Starting connection")
    # lightstreamer_client = LSClient("http://localhost:8080", "DEMO")
    lightstreamer_client = LSClient("http://push.lightstreamer.com", "DEMO")
    try:
        lightstreamer_client.connect()
    except Exception as e:
        print("Unable to connect to Lightstreamer Server")
        print(traceback.format_exc())
        sys.exit(1)

    # Making a new Subscription in MERGE mode
    subscription = Subscription(
        mode="MERGE",
        items=["item1", "item2", "item3", "item4",
               "item5", "item6", "item7", "item8",
               "item9", "item10", "item11", "item12"],
        fields=["stock_name", "last_price", "time", "bid", "ask"],
        adapter="QUOTE_ADAPTER")

    # Adding the "on_item_update" function to Subscription
    subscription.addlistener(on_item_update)

    # Registering the Subscription
    sub_key = lightstreamer_client.subscribe(subscription)

    input("{0:-^80}\n".format("HIT CR TO UNSUBSCRIBE AND DISCONNECT FROM \
    LIGHTSTREAMER"))

    # Unsubscribing from Lightstreamer by using the subscription key
    # lightstreamer_client.unsubscribe(sub_key)

    lightstreamer_client.unsubscribe()

    # Disconnecting
    lightstreamer_client.disconnect()


if __name__ == '__main__':
    main()
