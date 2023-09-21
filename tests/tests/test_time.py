import unittest
from mosaicpy.utils.time import parse_unixtime, to_unixtime


class TestTimeFunctions(unittest.TestCase):

    def test_to_unixtime(self):
        assert to_unixtime("2022-01-02 01:00:00") == 1641085200
        assert to_unixtime("2022-01-02 01:00:00",
                           timezone="Asia/Tokyo") == 1641052800
        assert to_unixtime("2022-01-01") == 1640995200
        assert to_unixtime("2022-01-01 01:00:00") == 1640998800
        assert to_unixtime("2022-01-01 12:00:00.000",
                           timezone="Asia/Shanghai") == 1641009600
        assert to_unixtime("2022-01-01T21:00:00+0600") == 1641049200


    def test_parse_unixtime(self):
        assert parse_unixtime(1641085200) == "2022-01-02 01:00:00" 
        assert parse_unixtime(1641085200, timezone="Asia/Tokyo") == "2022-01-02 10:00:00"
        assert parse_unixtime(1640995200, format="%Y-%m-%d") == "2022-01-01"
        assert parse_unixtime(1640998800, format="%Y-%m-%d %H:%M:%S") == "2022-01-01 01:00:00"
        assert parse_unixtime(1641009600, format="%Y-%m-%d %H:%M:%S.%f", timezone="Asia/Shanghai") == "2022-01-01 12:00:00.000000"
        assert parse_unixtime(1641049200, format="%Y-%m-%dT%H:%M:%S%z", timezone="Asia/Omsk") == "2022-01-01T21:00:00+0600"


if __name__ == "__main__":
    unittest.main()
