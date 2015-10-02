#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import traceback
import six

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    _HAS_PANDAS = False
    logger.warning("Can't import pandas")
else:
    _HAS_PANDAS = True

try:
    from infi.bunch import bunchify
except ImportError:
    _HAS_BUNCH = False
    logger.warning("Can't import bunch")
else:
    _HAS_BUNCH = True

def conv_resol(resolution):
    """Returns a string for resolution (from a Pandas)
    """
    if _HAS_PANDAS:
        from pandas.tseries.frequencies import to_offset
        d = {
            to_offset('1Min'):'MINUTE',
            to_offset('2Min'):'MINUTE_2',
            to_offset('3Min'):'MINUTE_3',
            to_offset('5Min'):'MINUTE_5',
            to_offset('10Min'):'MINUTE_10',
            to_offset('15Min'):'MINUTE_15',
            to_offset('30Min'): 'MINUTE_30',
            to_offset('1H'): 'HOUR',
            to_offset('2H'): 'HOUR_2',
            to_offset('3H'): 'HOUR_3',
            to_offset('4H'): 'HOUR_4',
            to_offset('D'): 'DAY',
            to_offset('W'): 'WEEK',
            to_offset('M'): 'MONTH'
        }
        offset = to_offset(resolution)
        if offset in d:
            return d[offset]
        else:
            logger.error(traceback.format_exc())
            logger.warning("conv_resol returns '%s'" % resolution)
            return resolution
    else:
        return resolution


def conv_datetime(dt, version=1):
    """Converts dt to string like
    version 1 = 2014:12:15-00:00:00
    version 2 = 2014-12-15-00:00:00
    """
    try:
        if isinstance(dt, six.string_types):
            if _HAS_PANDAS:
                import pandas as pd
                dt = pd.to_datetime(dt)

        d_formats = {
            1: "%Y:%m:%d-%H:%M:%S",
            2: "%Y-%m-%d %H:%M:%S"
        }
        fmt = d_formats[version]
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        logger.error(traceback.format_exc())
        logger.warning("conv_datetime returns %s" % dt)
        return dt


def conv_to_ms(td):
    """Converts td to integer number of milliseconds"""
    try:
        if isinstance(td, six.integer_types):
            return td
        else:
            return int(td.total_seconds() * 1000.0)
    except ValueError:
        logger.error(traceback.format_exc())
        logger.warning("conv_to_ms returns '%s'" % td)
        return td
