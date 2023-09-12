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


if __name__ == "__main__":
    unittest.main()
