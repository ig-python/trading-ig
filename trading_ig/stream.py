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
        self.lightstreamerEndpoint = None
        self.acc_number = None
        self.ls_client = None

    def create_session(self, encryption=False, version='2'):
        ig_session = self.ig_service.create_session(encryption=encryption, version=version)
        # if we have created a v3 session, we also need the session tokens
        if version == '3':
            self.ig_service.read_session(fetch_session_tokens='true')
        self.lightstreamerEndpoint = ig_session['lightstreamerEndpoint']
        cst = self.ig_service.session.headers['CST']
        xsecuritytoken = self.ig_service.session.headers['X-SECURITY-TOKEN']
        ls_password = "CST-%s|XST-%s" % (cst, xsecuritytoken)

        # Establishing a new connection to Lightstreamer Server
        logger.info("Starting connection with %s" % self.lightstreamerEndpoint)
        self.ls_client = LSClient(
            self.lightstreamerEndpoint, adapter_set="", user=self.acc_number, password=ls_password
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
