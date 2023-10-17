import unittest
# Replace 'your_module' with the actual module name
from mosaicpy.concurrent import parallel_map, parallel_map_lite


def my_function(x):
    return x * 2


class TestParallelMapLite(unittest.TestCase):

    def test_single_worker(self):
        result = parallel_map_lite(range(5), my_function, workers=1)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_multiple_workers(self):
        result = parallel_map_lite(range(5), my_function, workers=2)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_negative_workers(self):
        result = parallel_map_lite(range(5), my_function)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_empty_collection(self):
        result = parallel_map_lite([], my_function)
        self.assertEqual(result, [])


class TestParallelMap(unittest.TestCase):

    def test_single_worker(self):
        result = parallel_map(range(5), my_function, workers=1)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_multiple_workers(self):
        result = parallel_map(range(5), my_function, workers=2)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_negative_workers(self):
        result = parallel_map(range(5), my_function)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_empty_collection(self):
        result = parallel_map([], my_function)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
