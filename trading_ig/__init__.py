"""
IG Markets API Library for Python
https://github.com/ig-python/trading-ig/
by Femto Trader - https://github.com/femtotrader
"""

from .rest import IGService
from .stream import IGStreamService

__all__ = [
    "IGService",
    "IGStreamService",
]
