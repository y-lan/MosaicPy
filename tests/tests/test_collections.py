import unittest

from mosaicpy.collections import pmap, sample
from mosaicpy.collections.lists import sort_by_scores, values_to_rank


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


class TestSample(unittest.TestCase):
    def test_sample(self):
        d_dict = dict({str(x): x for x in range(10)})
        d_list = list(range(10))
        d_set = set(range(10))
        self.assertEqual(len(sample(d_dict, 3)), 3)
        self.assertEqual(len(sample(d_list, 3)), 3)
        self.assertEqual(len(sample(d_set, 3)), 3)


class TestLists(unittest.TestCase):
    def test_values_to_rank(self):
        scores = [4.5, 8.2, 3.1, 11.0]
        ranks = values_to_rank(scores)
        self.assertEqual(values_to_rank(scores), [1, 2, 0, 3])
        self.assertEqual(values_to_rank(scores, reverse=True), [2, 1, 3, 0])
        self.assertEqual(values_to_rank(scores, start_rank=1), [2, 3, 1, 4])

    def test_sort_by_scores(self):
        items = ['a', 'b', 'c', 'd']
        scores = [4.5, 8.2, 3.1, 11.0]
        self.assertEqual(sort_by_scores(items, scores), ['c', 'a', 'b', 'd'])
        self.assertEqual(sort_by_scores(
            items, scores, reverse=True), ['d', 'b', 'a', 'c'])


if __name__ == "__main__":
    unittest.main()
