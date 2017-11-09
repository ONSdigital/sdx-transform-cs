import unittest
from transform.transformers.InMemoryZip import InMemoryZip
import zipfile


class InMemoryZipTests(unittest.TestCase):

    def setUp(self):
        # use any file for the test
        with open("./tests/data/eq-mwss.json") as fb:
            self.test_data = fb.read()

    def test_get_filenames_returns_correct_filenames_in_correct_order(self):
        sut = InMemoryZip()
        expected_files = []
        file_count = 10
        for i in range(file_count):
            filename = "file_{0}".format(i)
            sut.append(filename, self.test_data)
            expected_files.append(filename)

        file_list = sut.get_filenames()

        self.assertEqual(file_list, expected_files)

    def test_filenames_with_subdirectories_are_stored_correctly(self):
        sut = InMemoryZip()
        expected_files = []
        file_count = 10
        for i in range(file_count):
            filename = r"\MyDir1\MyDir2\file_{0}".format(i)
            sut.append(filename, self.test_data)
            expected_files.append(filename)

        file_list = sut.get_filenames()

        self.assertEqual(file_list, expected_files)
        self.assertEqual(len(file_list), file_count)

    def test_file_contents_preserved_through_zip_and_unzip(self):
        sut = InMemoryZip()
        file_name = "Afile"
        sut.append(file_name, self.test_data)

        zip = sut.in_memory_zip

        z = zipfile.ZipFile(zip)
        file_content = z.open(file_name).read().decode('utf-8')

        self.assertEqual(file_content, self.test_data)
