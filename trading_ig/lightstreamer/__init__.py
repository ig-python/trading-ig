#!/usr/bin/python

#  Copyright 2014 Weswit s.r.l.
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

from __future__ import absolute_import, division, print_function

from trading_ig.lightstreamer.version import (__author__, __copyright__, __credits__,
                      __license__, __version__, __maintainer__, __email__,
                      __status__, __url__)

import logging
import threading
import time
import traceback
import trading_ig.compat as compat

CONNECTION_URL_PATH = "lightstreamer/create_session.txt"
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

logger = logging.getLogger(__name__)

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
        self._base_url = compat.parse_url(base_url)
        self._adapter_set = adapter_set
        self._user = user
        self._password = password
        self._session = {}
        self._subscriptions = {}
        self._current_subscription_key = 0
        self._stream_connection = None
        self._stream_connection_thread = None

    def _encode_params(self, params):
        """Encode the parameter for HTTP POST submissions, but
        only for non empty values..."""
        return compat._url_encode(
            dict([(k, v) for (k, v) in compat._iteritems(params) if v])
        )

    def _call(self, base_url, url, body):
        """Open a network connection and performs HTTP Post
        with provided body.
        """
        # Combines the "base_url" with the
        # required "url" to be used for the specific request.
        url = compat.urljoin(base_url.geturl(), url)
        #logger.debug("urlopen %s with data=%s" % (url, body))
        return compat._urlopen(url, data=self._encode_params(body)) # str_to_bytes

    def _set_control_link_url(self, custom_address=None):
        """Set the address to use for the Control Connection
        in such cases where Lightstreamer is behind a Load Balancer.
        """
        if custom_address is None:
            self._control_url = self._base_url
        else:
            parsed_custom_address = compat.parse_url("//" + custom_address)
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

    def _get_stream(self):
        """Read a single line of content of the Stream Connection."""
        line = self._stream_connection.readline().decode("utf-8").rstrip()
        return line

    def connect(self):
        """Establish a connection to Lightstreamer Server to create
        a new session.
        """
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
        server_response = self._get_stream()
        if server_response == OK_CMD:
            # Parsing session information
            while 1:
                line = self._get_stream()
                if line:
                    session_key, session_value = line.split(":", 1)
                    self._session[session_key] = session_value
                else:
                    break

            # Setup of the control link url
            self._set_control_link_url(self._session.get("ControlAddress"))

            # Start a new thread to handle real time updates sent
            # by Lightstreamer Server on the stream connection.
            self._stream_connection_thread = threading.Thread(
                name="STREAM-CONN-THREAD",
                target=self._receive
            )
            self._stream_connection_thread.setDaemon(True)
            self._stream_connection_thread.start()
        else:
            lines = self._stream_connection.readlines()
            lines.insert(0, server_response)
            logger.error("Server response error: \n%s" % "".join(lines))
            raise IOError()

    def _join(self):
        """Await the natural STREAM-CONN-THREAD termination."""
        if self._stream_connection_thread:
            logger.debug("Waiting for STREAM-CONN-THREAD to terminate")
            self._stream_connection_thread.join()
            self._stream_connection_thread = None
            logger.debug("STREAM-CONN-THREAD terminated")

    def disconnect(self):
        """Request to close the session previously opened with
        the connect() invocation.
        """
        if self._stream_connection is not None:
            # Close the HTTP connection
            self._stream_connection.close()
            logger.debug("Connection closed")
            #self._join()
            print("DISCONNECTED FROM LIGHTSTREAMER")
        else:
            logger.warning("No connection to Lightstreamer")

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
                logger.warning("No connection to Lightstreamer")

    def subscribe(self, subscription):
        """"Perform a subscription request to Lightstreamer Server."""
        # Register the Subscription with a new subscription key
        self._current_subscription_key += 1
        self._subscriptions[self._current_subscription_key] = subscription

        # Send the control request to perform the subscription
        self._control({
            "LS_Table": self._current_subscription_key,
            "LS_op": OP_ADD,
            "LS_data_adapter": subscription.adapter,
            "LS_mode": subscription.mode,
            "LS_schema": " ".join(subscription.field_names),
            "LS_id": " ".join(subscription.item_names),
        })
        return self._current_subscription_key

    def unsubscribe(self, subcription_key=None):
        """Unregister the Subscription associated to the
        specified subscription_key.
        if no subcription_key is given it unsubscribe all.
        """
        if subcription_key is None:
            subscriptions = self._subscriptions.copy() # To avoid a RuntimeError: dictionary changed size during iteration
            for subcription_key in subscriptions:
                self._unsubscribe(subcription_key)
        else:
            self._unsubscribe(subcription_key)

    def _unsubscribe(self, subcription_key):
        """Unregister the Subscription associated to the
        specified subscription_key.
        """
        if subcription_key in self._subscriptions:
            server_response = self._control({
                "LS_Table": subcription_key,
                "LS_op": OP_DELETE
            })
            logger.debug("Server response ---> <%s>", server_response)

            if server_response == OK_CMD:
                del self._subscriptions[subcription_key]
                logger.info("Unsubscribed successfully")
            else:
                logger.warning("Server error")
        else:
            logger.warning("No subscription key %d found!" % subcription_key)

    def _forward_update_message(self, update_message):
        """Forwards the real time update to the relative
        Subscription instance for further dispatching to its listeners.
        """
        logger.debug("Received update message ---> <%s>", update_message)
        tok = update_message.split(',')
        table, item = int(tok[0]), tok[1]
        if table in self._subscriptions:
            self._subscriptions[table].notifyupdate(item)
        else:
            logger.warning("No subscription found!")


    def _receive(self):
        receive = True
        while receive:
            logger.debug("Waiting for a new message")
            try:
                message = self._get_stream()
                logger.debug("Received message ---> <%s>" % message)
            except Exception:
                logger.error("Communication error")
                print(traceback.format_exc())
                message = None

            if message is None:
                receive = False
                logger.warning("No new message received")
            elif message == PROBE_CMD:
                # Skipping the PROBE message, keep on receiving messages.
                logger.debug("PROBE message")
            elif message.startswith(ERROR_CMD):
                # Terminate the receiving loop on ERROR message
                receive = False
                logger.error("ERROR")
            elif message.startswith(LOOP_CMD):
                # Terminate the the receiving loop on LOOP message.
                # A complete implementation should proceed with
                # a rebind of the session.
                logger.debug("LOOP")
                receive = False
            elif message.startswith(SYNC_ERROR_CMD):
                # Terminate the receiving loop on SYNC ERROR message.
                # A complete implementation should create a new session
                # and re-subscribe to all the old items and relative fields.
                logger.error("SYNC ERROR")
                receive = False
            elif message.startswith(END_CMD):
                # Terminate the receiving loop on END message.
                # The session has been forcibly closed on the server side.
                # A complete implementation should handle the
                # "cause_code" if present.
                logger.info("Connection closed by the server")
                receive = False
            elif message.startswith("Preamble"):
                # Skipping Preamble message, keep on receiving messages.
                logger.debug("Preamble")
            else:
                self._forward_update_message(message)

        logger.debug("Closing connection")
        # Clear internal data structures for session
        # and subscriptions management.
        #self._stream_connection.close()
        self._stream_connection = None
        self._session.clear()
        self._subscriptions.clear()
        self._current_subscription_key = 0
