import unittest
import os
from mosaicpy.utils.file import load_jsonl, dump_jsonl


class TestJsonlFunctions(unittest.TestCase):
    def setUp(self):
        # Set up the test environment.
        self.test_file_path = "test.jsonl"
        self.test_data = [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}]

    def test_dump_and_load_jsonl(self):
        for file_path in [self.test_file_path, self.test_file_path + ".gz"]:
            dump_jsonl(self.test_data, file_path)

            self.assertTrue(os.path.exists(file_path))

            loaded_data = load_jsonl(file_path)
            self.assertEqual(loaded_data, self.test_data)

            loaded_data_2 = load_jsonl(
                file_path,
                cb_func=lambda x: x if x["key"] != "value1" else None,
                skip_none=True,
            )
            self.assertEqual(loaded_data_2, self.test_data[1:])

            if os.path.exists(file_path):
                os.remove(file_path)

    def tearDown(self):
        # Clean up the test environment.
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)


if __name__ == "__main__":
    unittest.main()
