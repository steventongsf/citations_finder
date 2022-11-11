from collections import defaultdict
from typing import ByteString
import unittest

from config import Config
from journal_finder import _getExistingJournals, _getGBIFResults, _getCrossrefResults

# Test journal_finder methods
class JournalFinderTests(unittest.TestCase):
    #config_file = "./test_data/config.ini"
    max_size = 10 # max results to fetch from remote url
    gbfi_link = f"https://api.gbif.org/v1/literature/search?contentType=literature&year=2021,2021&literatureType=journal&gbifDatasetKey=f934f8e2-32ca-46a7-b2f8-b032a4740454&limit={max_size}"

    def setUp(self):
        self.cfg = Config()

    # test loading journal dois from journal tsv file
    def test_getExistingJournals_validDict(self):
        actual = _getExistingJournals("./test_data/journals.proceeds.tsv")
        expected = {'0027-8424': None, '1091-6490': None}
        self.assertEqual(expected, actual)

    # get list of gbif urls for fetching published works
    def test_config_gbif_api_collection_links_values(self):
        links = self.cfg.get_list('journal population', 'gbif_api_collection_links')
        self.assertTrue(len(links) == 3)
        for link in links:
            self.assertTrue("https://api.gbif.org/v1/literature/search" in link)

    # test fetching published works from gbif.org
    # not sure if data changes over time even for past years but it could cause this test to fail
    def test_getGBIFResults(self):
        result = _getGBIFResults(self.gbfi_link)
        row = result[0]
        self.assertTrue(len(result) >= 10)
        self.assertTrue(len(row["authors"]) >= 6)
        self.assertTrue("IN" in row["countriesOfCoverage"])
        for row in result:
           #print(row)
           pass
    
    def test_getCrossrefResults_noMissingTitles(self):
        test_doi = "10.1111/jeb.13941"
        test_title = "Journal of Evolutionary Biology"
        journal_dict = defaultdict()
        journal_dict[test_title] = []
        journal_dict = _getCrossrefResults(test_doi, journal_dict)
        self.assertEquals([], journal_dict[test_title])

    @unittest.skip("test fails when title is not in list")
    def test_getCrossrefResults_missingTitles(self):
        test_doi = "10.1111/jeb.13941"
        test_title = "of Evolutionary Biology"
        journal_dict = defaultdict()
        journal_dict[test_title] = []
        journal_dict = _getCrossrefResults(test_doi, journal_dict)

    def test_findISSNByJournalTitle(self):
        pass