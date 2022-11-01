import unittest

from config import Config
from journal_finder import _getExistingJournals, _getGBIFResults

# Test journal_finder methods
class JournalFinderTests(unittest.TestCase):
    config_file = "./test_data/config.ini"

    def setUp(self):
        self.cfg = Config()

    def test_getExistingJournals_valid_dict(self):
        actual = _getExistingJournals("./test_data/journals.proceeds.tsv")
        expected = {'0027-8424': None, '1091-6490': None}
        self.assertEqual(expected, actual)

    def test_config_gbif_api_collection_links_value(self):
        links = self.cfg.get_list('journal population', 'gbif_api_collection_links')
        self.assertTrue(len(links) == 3)

    def test_getGBIFResults(self):
        links = self.cfg.get_list('journal population', 'gbif_api_collection_links')
        result = _getGBIFResults(links[0])
        self.assertTrue(len(result) > 0)
