import warnings

import pytest

from trading_ig.utils import conv_datetime, conv_resol

try:
    import pandas  # noqa

    pandas_installed = True
except ImportError:
    pandas_installed = False

"""
Unit tests for utils module
"""


class TestUtils:
    def test_conv_datetime_format_1(self):
        result = conv_datetime("2020/03/01", 1)
        assert result == "2020:03:01-00:00:00"

    def test_conv_datetime_format_2(self):
        result = conv_datetime("2020/03/01", 2)
        assert result == "2020/03/01 00:00:00"

    def test_conv_datetime_format_3(self):
        result = conv_datetime("2020/03/01", 3)
        assert result == "2020/03/01 00:00:00"

    @pytest.mark.skipif(not pandas_installed, reason="Requires pandas")
    @pytest.mark.parametrize(
        "resolution,expected",
        [
            ("1s", "SECOND"),
            ("1Min", "MINUTE"),
            ("2Min", "MINUTE_2"),
            ("3Min", "MINUTE_3"),
            ("5Min", "MINUTE_5"),
            ("10Min", "MINUTE_10"),
            ("15Min", "MINUTE_15"),
            ("30Min", "MINUTE_30"),
            ("1h", "HOUR"),
            ("2h", "HOUR_2"),
            ("3h", "HOUR_3"),
            ("4h", "HOUR_4"),
            ("D", "DAY"),
            ("W", "WEEK"),
            ("ME", "MONTH"),
        ],
    )
    def test_conv_resol(self, resolution, expected):
        assert conv_resol(resolution) == expected

    @pytest.mark.skipif(not pandas_installed, reason="Requires pandas")
    @pytest.mark.parametrize(
        "resolution,expected",
        [
            ("1H", "HOUR"),
            ("2H", "HOUR_2"),
            ("3H", "HOUR_3"),
            ("4H", "HOUR_4"),
            ("M", "MONTH"),
        ],
    )
    def test_conv_resol_legacy_alias(self, resolution, expected):
        """The 'H' and 'M' aliases were removed in pandas 3.0, but they are the
        spellings this library has always documented, so they must keep working"""
        assert conv_resol(resolution) == expected

    @pytest.mark.skipif(not pandas_installed, reason="Requires pandas")
    def test_conv_resol_legacy_alias_does_not_warn(self):
        """Legacy aliases are normalised before pandas sees them, so they don't
        trigger the pandas 2 deprecation warning"""
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            assert conv_resol("1H") == "HOUR"

    @pytest.mark.skipif(not pandas_installed, reason="Requires pandas")
    @pytest.mark.parametrize("resolution", ["2D", "2W", "12h"])
    def test_conv_resol_unsupported(self, resolution):
        """A valid pandas offset that IG has no resolution for is returned
        unchanged"""
        assert conv_resol(resolution) == resolution

    @pytest.mark.skipif(not pandas_installed, reason="Requires pandas")
    @pytest.mark.parametrize("resolution", ["banana", "", "X"])
    def test_conv_resol_invalid(self, resolution):
        """Anything pandas can't parse at all raises, rather than being passed
        on to the API. Used e.g. in
        test_historical_prices_v3_num_points_bad_resolution"""
        with pytest.raises(ValueError):
            conv_resol(resolution)
