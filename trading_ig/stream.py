#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import sys
import traceback
import logging

from lightstreamer.client import LightstreamerClient, Subscription

logger = logging.getLogger(__name__)


class IGStreamService(object):
    def __init__(self, ig_service):
        self.ig_service = ig_service
        self.lightstreamerEndpoint = None
        self.acc_number = None
        self.ls_client = None

    def create_session(self, encryption=False, version="2"):
        ig_session = self.ig_service.create_session(
            encryption=encryption, version=version
        )
        # if we have created a v3 session, we also need the session tokens
        if version == "3":
            self.ig_service.read_session(fetch_session_tokens="true")
        self.lightstreamerEndpoint = ig_session["lightstreamerEndpoint"]
        cst = self.ig_service.session.headers["CST"]
        xsecuritytoken = self.ig_service.session.headers["X-SECURITY-TOKEN"]
        ls_password = "CST-%s|XST-%s" % (cst, xsecuritytoken)

        # Establishing a new connection to Lightstreamer Server
        logger.info("Starting connection with %s" % self.lightstreamerEndpoint)
        self.ls_client = LightstreamerClient(self.lightstreamerEndpoint, None)
        self.ls_client.connectionDetails.setUser(self.acc_number)
        self.ls_client.connectionDetails.setPassword(ls_password)
        try:
            self.ls_client.connect()
            return
        except Exception:
            logger.error("Unable to connect to Lightstreamer Server")
            logger.error(traceback.format_exc())
            sys.exit(1)

    def subscribe(self, subscription: Subscription):
        self.ls_client.subscribe(subscription)

    def unsubscribe_all(self):
        # To avoid a RuntimeError: dictionary changed size during iteration
        subscriptions = self.ls_client.getSubscriptions().copy()
        for sub in subscriptions:
            self.ls_client.unsubscribe(sub)

    def disconnect(self):
        self.unsubscribe_all()
        self.ls_client.disconnect()
