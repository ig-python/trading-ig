#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import sys
import traceback
import logging

from .lightstreamer import LSClient

logger = logging.getLogger(__name__)


class IGStreamService(object):
    def __init__(self, ig_service):
        self.ig_service = ig_service
        self.ig_session = None
        self.ls_client = None

    def create_session(self, encryption=False):
        ig_session = self.ig_service.create_session(encryption=encryption)
        self.ig_session = ig_session
        return ig_session

    def connect(self, accountId):
        cst = self.ig_service.crud_session.CLIENT_TOKEN
        xsecuritytoken = self.ig_service.crud_session.SECURITY_TOKEN
        lightstreamerEndpoint = self.ig_session[u"lightstreamerEndpoint"]
        # clientId = self.ig_session[u'clientId']
        ls_password = "CST-%s|XST-%s" % (cst, xsecuritytoken)

        # Establishing a new connection to Lightstreamer Server
        logger.info("Starting connection with %s" % lightstreamerEndpoint)
        # self.ls_client = LSClient("http://localhost:8080", "DEMO")
        # self.ls_client = LSClient("http://push.lightstreamer.com", "DEMO")
        self.ls_client = LSClient(
            lightstreamerEndpoint, adapter_set="", user=accountId, password=ls_password
        )
        try:
            self.ls_client.connect()
            return
        except Exception:
            logger.error("Unable to connect to Lightstreamer Server")
            logger.error(traceback.format_exc())
            sys.exit(1)

    def unsubscribe_all(self):
        # To avoid a RuntimeError: dictionary changed size during iteration
        subscriptions = self.ls_client._subscriptions.copy()
        for subcription_key in subscriptions:
            self.ls_client.unsubscribe(subcription_key)

    def disconnect(self):
        self.unsubscribe_all()
        self.ls_client.disconnect()
