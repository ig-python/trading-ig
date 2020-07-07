#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import logging
import traceback
import six

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    _HAS_PANDAS = False
    logger.info("Can't import pandas")
else:
    _HAS_PANDAS = True

try:
    from munch import munchify  # noqa
except ImportError:
    _HAS_MUNCH = False
    logger.info("Can't import munch")
else:
    _HAS_MUNCH = True


DATE_FORMATS = {1: "%Y:%m:%d-%H:%M:%S", 2: "%Y/%m/%d %H:%M:%S", 3: "%Y/%m/%d %H:%M:%S"}


def conv_resol(resolution):
    """Returns a string for resolution (from a Pandas)
    """
    if _HAS_PANDAS:
        to_offset = lambda x : x

        d = {
            to_offset("1min"): "MINUTE",
            to_offset("2min"): "MINUTE_2",
            to_offset("3min"): "MINUTE_3",
            to_offset("5min"): "MINUTE_5",
            to_offset("10min"): "MINUTE_10",
            to_offset("15min"): "MINUTE_15",
            to_offset("30min"): "MINUTE_30",
            to_offset("1h"): "HOUR",
            to_offset("2h"): "HOUR_2",
            to_offset("3h"): "HOUR_3",
            to_offset("4h"): "HOUR_4",
            to_offset("1d"): "DAY",
            to_offset("1w"): "WEEK",
            to_offset("1m"): "MONTH",
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


def conv_datetime(dt, version=2):
    """Converts dt to string like
    version 1 = 2014:12:15-00:00:00
    version 2 = 2014/12/15 00:00:00
    version 3 = 2014/12/15 00:00:00
    """
    try:
        if isinstance(dt, six.string_types):
            if _HAS_PANDAS:
                dt = pd.to_datetime(dt)

        fmt = DATE_FORMATS[int(version)]
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


def remove(cache):
    """Remove cache"""
    try:
        filename = "%s.sqlite" % cache
        print("remove %s" % filename)
        os.remove(filename)
    except Exception:
        pass
