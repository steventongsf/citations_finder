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
# query for published journals and update journals.tsv
def main():
    config = Config()
    # create tables
    CrossrefJournalEntry.create_tables()
    downloaders = Downloaders()
    downloaders.create_tables()
    # make sure journals are written
    gbif_url_list = config.get_list('journal population', 'gbif_api_collection_links')
    for url in gbif_url_list:
        logging.info(f"Processing journals for population from link: {url}")
        journal_finder.addJournals('journals.tsv', url)

main()