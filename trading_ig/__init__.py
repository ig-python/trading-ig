#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
IG Markets API Library for Python
https://github.com/ig-python/ig-markets-api-python-library/
by Femto Trader - https://github.com/femtotrader
"""

from __future__ import absolute_import, division, print_function


from .rest import IGService
from .stream import IGStreamService

__all__ = [
    "IGService",
    "IGStreamService",
]
