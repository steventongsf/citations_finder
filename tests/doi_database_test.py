import unittest

from crossref_journal_entry import CrossrefJournalEntry
from doi_database import DoiDatabase
from doi_entry import DoiEntry
from scan_database import ScanDatabase
from validator import Validator




class DoiDatabaseTest(unittest.TestCase):

    def setUp(self):
        pass

    def test(self):
        self.db = DoiDatabase(2021,2022)
