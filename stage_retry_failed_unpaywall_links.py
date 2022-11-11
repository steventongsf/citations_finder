from doi_entry import DoiFactory
import sys
from doi_database import DoiDatabase
from database_report import DatabaseReport
from scan_database import ScanDatabase
from known_good_papers import KnownGoodPapers
from scan import Scan
from validator import Validator
from config import Config
from downloaders import Downloaders
from copyout import CopyOut
from crossref_journal_entry import CrossrefJournalEntry
import journal_finder
import logging
import main as main

config = Config()
# create tables
CrossrefJournalEntry.create_tables()
downloaders = Downloaders()
downloaders.create_tables()
main.retry_failed_unpaywall_links(config)