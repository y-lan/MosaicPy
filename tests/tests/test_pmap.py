import unittest
from mosaicpy.collections import pmap


def my_function(x):
    return x * 2


class TestParallelMapLite(unittest.TestCase):

    def test_single_worker(self):
        result = pmap(range(5), my_function, workers=1)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_multiple_workers(self):
        result = pmap(range(5), my_function, workers=2)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_progress_bar(self):
        result = pmap(range(5), my_function, workers=2, show_progress=True)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_negative_workers(self):
        result = pmap(range(5), my_function)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_empty_collection(self):
        result = pmap([], my_function)
        self.assertEqual(result, [])


class TestParallelMap(unittest.TestCase):

    def test_single_worker(self):
        result = pmap(range(5), my_function, workers=1, use_process=True)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_multiple_workers(self):
        result = pmap(range(5), my_function, workers=2, use_process=True)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_progress_bar(self):
        result = pmap(range(5), my_function, workers=2,
                      use_process=True, show_progress=True)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_negative_workers(self):
        result = pmap(range(5), my_function, use_process=True)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_empty_collection(self):
        result = pmap([], my_function, use_process=True)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
