from trading_ig.utils import conv_datetime

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
