#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

if PY3:
    from urllib.request import urlopen as _urlopen
    from urllib.parse import (urlparse as parse_url, urlunparse, urljoin, urlencode)

    def _url_encode(params):
        return urlencode(params).encode("utf-8")

    def _iteritems(d):
        return iter(d.items())

    wait_for_input = input

else:
    from urllib import (urlopen as _urlopen, urlencode)
    from urlparse import urlparse as parse_url
    from urlparse import urlunparse, urljoin

    def _url_encode(params):
        return urlencode(params)

    def _iteritems(d):
        return d.iteritems()

    wait_for_input = raw_input
