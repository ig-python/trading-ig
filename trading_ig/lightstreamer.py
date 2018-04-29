#!/usr/bin/python3

#  Copyright (c) Lightstreamer Srl.
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

import logging
import threading
import traceback

from six.moves.urllib.request import urlopen as _urlopen
from six.moves.urllib.parse import (urlparse as parse_url, urljoin, urlencode)

try:
    from systemd.daemon import notify
except ImportError:
    notify = None


def _url_encode(params):
    return urlencode(params).encode("utf-8")


def _iteritems(d):
    return iter(d.items())


CONNECTION_URL_PATH = "lightstreamer/create_session.txt"
BIND_URL_PATH = "lightstreamer/bind_session.txt"
CONTROL_URL_PATH = "lightstreamer/control.txt"
# Request parameter to create and activate a new Table.
OP_ADD = "add"
# Request parameter to delete a previously created Table.
OP_DELETE = "delete"
# Request parameter to force closure of an existing session.
OP_DESTROY = "destroy"
# List of possible server responses
PROBE_CMD = "PROBE"
END_CMD = "END"
LOOP_CMD = "LOOP"
ERROR_CMD = "ERROR"
SYNC_ERROR_CMD = "SYNC ERROR"
OK_CMD = "OK"

log = logging.getLogger(__name__)


class Subscription(object):
    """Represents a Subscription to be submitted to a Lightstreamer Server."""

    def __init__(self, mode, items, fields, adapter=""):
        self.item_names = items
        self._items_map = {}
        self.field_names = fields
        self.adapter = adapter
        self.mode = mode
        self.snapshot = "true"
        self._listeners = []

    def _decode(self, value, last):
        """Decode the field value according to
        Lightstremar Text Protocol specifications.
        """
        if value == "$":
            return u''
        elif value == "#":
            return None
        elif not value:
            return last
        elif value[0] in "#$":
            value = value[1:]

        return value

    def addlistener(self, listener):
        self._listeners.append(listener)

    def notifyupdate(self, item_line):
        """Invoked by LSClient each time Lightstreamer Server pushes
        a new item event.
        """
        # Tokenize the item line as sent by Lightstreamer
        toks = item_line.rstrip('\r\n').split('|')
        undecoded_item = dict(list(zip(self.field_names, toks[1:])))

        # Retrieve the previous item stored into the map, if present.
        # Otherwise create a new empty dict.
        item_pos = int(toks[0])
        curr_item = self._items_map.get(item_pos, {})
        # Update the map with new values, merging with the
        # previous ones if any.
        self._items_map[item_pos] = dict([
            (k, self._decode(v, curr_item.get(k))) for k, v
            in list(undecoded_item.items())
        ])
        # Make an item info as a new event to be passed to listeners
        item_info = {
            'pos': item_pos,
            'name': self.item_names[item_pos - 1],
            'values': self._items_map[item_pos]
        }

        # Update each registered listener with new event
        for on_item_update in self._listeners:
            on_item_update(item_info)


class LSClient(object):
    """Manages the communication with Lightstreamer Server"""

    def __init__(self, base_url, adapter_set="", user="", password=""):
        self._base_url = parse_url(base_url)
        self._adapter_set = adapter_set
        self._user = user
        self._password = password
        self._session = {}
        self._subscriptions = {}
        self._current_subscription_key = 0
        self._stream_connection = None
        self._stream_connection_thread = None
        self._bind_counter = 0

    def _encode_params(self, params):
        """Encode the parameter for HTTP POST submissions, but
        only for non empty values..."""
        return _url_encode(
            dict([(k, v) for (k, v) in _iteritems(params) if v])
        )

    def _call(self, base_url, url, body):
        """Open a network connection and performs HTTP Post
        with provided body.
        """
        # Combines the "base_url" with the
        # required "url" to be used for the specific request.
        url = urljoin(base_url.geturl(), url)
        return _urlopen(url, data=self._encode_params(body))

    def _set_control_link_url(self, custom_address=None):
        """Set the address to use for the Control Connection
        in such cases where Lightstreamer is behind a Load Balancer.
        """
        if custom_address is None:
            self._control_url = self._base_url
        else:
            parsed_custom_address = parse_url("//" + custom_address)
            self._control_url = parsed_custom_address._replace(
                scheme=self._base_url[0]
            )

    def _control(self, params):
        """Create a Control Connection to send control commands
        that manage the content of Stream Connection.
        """
        params["LS_session"] = self._session["SessionId"]
        response = self._call(self._control_url, CONTROL_URL_PATH, params)
        return response.readline().decode("utf-8").rstrip()

    def _read_from_stream(self):
        """Read a single line of content of the Stream Connection."""
        line = self._stream_connection.readline().decode("utf-8").rstrip()
        return line

    def connect(self):
        """Establish a connection to Lightstreamer Server to create
        a new session.
        """

        if not notify:
            log.warning("systemd.daemon not available, "
                        + "no watchdog notifications will be sent.")

        self._stream_connection = self._call(
            self._base_url,
            CONNECTION_URL_PATH,
            {
                "LS_op2": 'create',
                "LS_cid": 'mgQkwtwdysogQz2BJ4Ji kOj2Bg',
                "LS_adapter_set": self._adapter_set,
                "LS_user": self._user,
                "LS_password": self._password}
        )
        stream_line = self._read_from_stream()
        self._handle_stream(stream_line)

    def bind(self):
        """Replace a completely consumed connection in listening for an active
        Session.
        """
        self._stream_connection = self._call(
            self._control_url,
            BIND_URL_PATH,
            {
                "LS_session": self._session["SessionId"]
            }
        )

        self._bind_counter += 1
        stream_line = self._read_from_stream()
        self._handle_stream(stream_line)

    def _handle_stream(self, stream_line):
        if stream_line == OK_CMD:
            # Parsing session inkion
            while 1:
                next_stream_line = self._read_from_stream()
                if next_stream_line:
                    session_key, session_value = next_stream_line.split(":", 1)
                    self._session[session_key] = session_value
                else:
                    break

            # Setup of the control link url
            self._set_control_link_url(self._session.get("ControlAddress"))

            # Start a new thread to handle real time updates sent
            # by Lightstreamer Server on the stream connection.
            self._stream_connection_thread = threading.Thread(
                name="STREAM-CONN-THREAD-{0}".format(self._bind_counter),
                target=self._receive
            )
            self._stream_connection_thread.setDaemon(True)
            self._stream_connection_thread.start()
        else:
            lines = self._stream_connection.readlines()
            lines.insert(0, stream_line)
            log.error("Server response error: \n{0}".format("".join(lines)))
            raise IOError()

    def _join(self):
        """Await the natural STREAM-CONN-THREAD termination."""
        if self._stream_connection_thread:
            log.debug("Waiting for thread to terminate")
            self._stream_connection_thread.join()
            self._stream_connection_thread = None
            log.debug("Thread terminated")

    def disconnect(self):
        """Request to close the session previously opened with
        the connect() invocation.
        """
        if self._stream_connection is not None:
            # Close the HTTP connection
            self._stream_connection.close()
            log.debug("Connection closed")
            print("DISCONNECTED FROM LIGHTSTREAMER")
        else:
            log.warning("No connection to Lightstreamer")

    def destroy(self):
        """Destroy the session previously opened with
        the connect() invocation.
        """
        if self._stream_connection is not None:
            server_response = self._control({"LS_op": OP_DESTROY})
            if server_response == OK_CMD:
                # There is no need to explicitly close the connection,
                # since it is handled by thread completion.
                self._join()
            else:
                log.warning("No connection to Lightstreamer")

    def subscribe(self, subscription):
        """"Perform a subscription request to Lightstreamer Server."""
        # Register the Subscription with a new subscription key
        self._current_subscription_key += 1
        self._subscriptions[self._current_subscription_key] = subscription

        # Send the control request to perform the subscription
        server_response = self._control({
            "LS_Table": self._current_subscription_key,
            "LS_op": OP_ADD,
            "LS_data_adapter": subscription.adapter,
            "LS_mode": subscription.mode,
            "LS_schema": " ".join(subscription.field_names),
            "LS_id": " ".join(subscription.item_names),
        })
        log.debug("Server response ---> <{0}>".format(server_response))
        return self._current_subscription_key

    def unsubscribe(self, subcription_key):
        """Unregister the Subscription associated to the
        specified subscription_key.
        """
        if subcription_key in self._subscriptions:
            server_response = self._control({
                "LS_Table": subcription_key,
                "LS_op": OP_DELETE
            })
            log.debug("Server response ---> <{0}>".format(server_response))

            if server_response == OK_CMD:
                del self._subscriptions[subcription_key]
                log.info("Unsubscribed successfully")
            else:
                log.warning("Server error")
        else:
            log.warning("No subscription key {0} found!".format(
                        subcription_key))

    def _forward_update_message(self, update_message):
        """Forwards the real time update to the relative
        Subscription instance for further dispatching to its listeners.
        """
        log.debug("Received update message ---> <{0}>".format(update_message))
        tok = update_message.split(',', 1)
        table, item = int(tok[0]), tok[1]
        if table in self._subscriptions:
            self._subscriptions[table].notifyupdate(item)
        else:
            log.warning("No subscription found!")

    def _receive(self):
        rebind = False
        receive = True
        while receive:
            log.debug("Waiting for a new message")
            try:
                message = self._read_from_stream()
                log.debug("Received message ---> <{0}>".format(message))
            except Exception:
                log.error("Communication error")
                print(traceback.format_exc())
                message = None

            if notify:
                notify('WATCHDOG=1')

            if message is None:
                receive = False
                log.warning("No new message received")
            elif message == PROBE_CMD:
                # Skipping the PROBE message, keep on receiving messages.
                log.debug("PROBE message")
            elif message.startswith(ERROR_CMD):
                # Terminate the receiving loop on ERROR message
                receive = False
                log.error("ERROR")
            elif message.startswith(LOOP_CMD):
                # Terminate the the receiving loop on LOOP message.
                # A complete implementation should proceed with
                # a rebind of the session.
                log.debug("LOOP")
                receive = False
                rebind = True
            elif message.startswith(SYNC_ERROR_CMD):
                # Terminate the receiving loop on SYNC ERROR message.
                # A complete implementation should create a new session
                # and re-subscribe to all the old items and relative fields.
                log.error("SYNC ERROR")
                receive = False
            elif message.startswith(END_CMD):
                # Terminate the receiving loop on END message.
                # The session has been forcibly closed on the server side.
                # A complete implementation should handle the
                # "cause_code" if present.
                log.info("Connection closed by the server")
                receive = False
            elif message.startswith("Preamble"):
                # Skipping Preamble message, keep on receiving messages.
                log.debug("Preamble")
            else:
                self._forward_update_message(message)

        self._stream_connection = None
        if not rebind:
            log.debug("Closing connection")
            # Clear internal data structures for session
            # and subscriptions management.
            self._stream_connection.close()
            self._session.clear()
            self._subscriptions.clear()
            self._current_subscription_key = 0
        else:
            log.debug("Binding to this active session")
            self.bind()


if __name__ == "__main__":
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
        import sys
        sys.exit(1)

    # Making a new Subscription in MERGE mode
    subscription = Subscription(
        mode="MERGE",
        items=["item1", "item2", "item3", "item4",
               "item5", "item6", "item7", "item8",
               "item9", "item10", "item11", "item12"],
        fields=["stock_name", "last_price", "time", "bid", "ask"],
        adapter="QUOTE_ADAPTER")

    # A simple function acting as a Subscription listener
    def on_item_update(item_update):
        print("{stock_name:<19}: Last{last_price:>6} - Time {time:<8} - "
              "Bid {bid:>5} - Ask {ask:>5}".format(**item_update["values"]))

    # Adding the "on_item_update" function to Subscription
    subscription.addlistener(on_item_update)

    # Registering the Subscription
    sub_key = lightstreamer_client.subscribe(subscription)

    def handler():
        # Unsubscribing from Lightstreamer by using the subscription key
        lightstreamer_client.unsubscribe(sub_key)
        # Disconnecting
        lightstreamer_client.disconnect()

    import atexit
    atexit.register(handler)

    lightstreamer_client._join()
