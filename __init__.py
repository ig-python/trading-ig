#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
IG Markets API Library for Python
https://github.com/ig-python/ig-markets-api-python-library/
by Femto Trader - https://github.com/femtotrader
"""

from __future__ import absolute_import, division, print_function


from .version import (__author__, __copyright__, __credits__, __license__,
                      __version__, __maintainer__, __email__, __status__,
                      __url__)

from .rest import IGService
from .stream import IGStreamService

__all__ = ['IGService', 'IGStreamService', '__author__',
           '__copyright__', '__credits__', '__license__',
           '__version__', '__maintainer__', '__email__',
           '__status__', '__url__']
