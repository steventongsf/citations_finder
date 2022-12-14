import os

import requests.exceptions

from doi_entry import DoiEntry
from doi_entry import DoiFactory
from utils_mixin import Utils
import glob
import urllib
import time
import csv
from crossref_journal_entry import CrossrefJournalEntry
from doi_entry import EntryExistsException
from db_connection import DBConnection
from database_report import DatabaseReport
from downloaders import Downloaders
from scan_database import ScanDatabase
from validator import Validator

from datetime import date
import logging

class RetriesExceededException(Exception):
    pass


class DoiDatabase(Utils):
    headers = {
        'User-Agent': 'development; mailto:jrussack@calacademy.org',
    }

    # "do_setup" creates the db tables (if they don't exist) and polls crossref.org for
    # the journals listed in journals.tsv. If the PDF already exists
    # then the full path is updated.
    #
    # "do_download" scans through all DOI records. If the PDF is already
    # downloaded, it populates the record accordingly.
    def __init__(self,
                 start_year=None,
                 end_year=None):
        super().__init__()

        self._setup()
        if start_year is not None:
            assert end_year is not None, "If scanning must provide both a start and an end year"
            self._query_journals(start_year, end_year)

    def _setup(self):
        CrossrefJournalEntry.create_tables()
        DoiEntry.create_tables()
        ScanDatabase.create_tables()
        Validator.create_tables()

    # Queries crossref for the history of the journal in question.
    # Crossref returns all records starting at the start_year until the
    # most recent year.

    # Updates the table "journals" with the "start year" passed in here
    # and "end year" being the current year. Journals table doesn't get an
    # entry until an attempt to query DOIs from crossref has happened.
    def _query_journals(self, start_year, end_year):
        with open('journals.tsv', 'r') as tsvin:
            for line in csv.reader(tsvin, delimiter='\t'):
                try:
                    if len(line) == 0 or line[0].startswith('#'):
                        continue
                    issn = line[0]
                    if issn.startswith("not in crossref"):
                        logging.warning("Not in crossref, continuing.")
                        continue
                    journal = line[1]
                    type = None
                    if len(line) > 2:
                        type = line[2]
                except Exception as e:
                    logging.warning(f"Parsing error: {line}, skipping.")
                    continue

                logging.info(f"Downloading {journal} issn: {issn} starting year: {start_year} ending year {end_year}")
                if type is None:
                    logging.info("")
                else:
                    logging.info(f" Type: {type}")

                if self._check_journal_record(issn, start_year):
                    self.download_issn(issn, start_year, end_year)
                    self._update_journal_record(issn, start_year, journal, type)

    def force_crossref_update(self, start_year):
        end_year = start_year
        query = f"select issn,name,type from journals"
        results = DBConnection.execute_query(query)
        for jounral in results:
            issn = jounral[0]
            name = jounral[1]
            type = jounral[2]
            self.download_issn(issn, start_year, end_year)
            self._update_journal_record(issn, start_year, name, type)

    def _get_issn_oldest_year(self, issn):
        query = f"select start_year from journals where issn=\"{issn}\""
        results = DBConnection.execute_query(query)

        if len(results) >= 1:
            return int(results[0][0])
        else:
            return None

    # returns true if the journal needs to be downloaded
    def _check_journal_record(self, issn, start_year):

        oldest_year_downloaded = self._get_issn_oldest_year(issn)
        if oldest_year_downloaded is None or (oldest_year_downloaded > start_year):
            return True
        return False

    def _update_journal_record(self, issn, start_year, name, type):
        previous_start_year = self._get_issn_oldest_year(issn)
        if previous_start_year is None or previous_start_year > start_year:
            name = name.replace("'", "''")
            logging.info(f"{issn}\t{name}\t{type}")
            sql = f"INSERT OR REPLACE INTO journals (issn,name, type,start_year,end_year) VALUES ('{issn}','{name}','{type}',{start_year},{date.today().year})"
            results = DBConnection.execute_query(sql)

    # not referenced anywhere at present; invoke from main per README

    # Scans through existing PDFs in the directory
    # If they're present, create or update the DoiEntry
    # in the database.

    # Inefficent; single request to crossref.org to get metadata for one pub.
    # it's better to run download_issn for the journal of interest and the run
    # import_pdfs. If the pdfs are of unknown or mixed provenance, then this
    # is the way to go.

    def import_pdfs(self, directory="./", raise_exception_if_exist=True):
        pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
        total_count = 0
        for pdf_file in pdf_files:
            doi_string = self.get_doi_from_path(pdf_file)
            base_url = f"https://api.crossref.org/works/{doi_string}"

            logging.info(f"Querying crossref.org for metadata to build db: {base_url}")
            results = self._get_url_(base_url)
            item = results['message']
            if raise_exception_if_exist:
                DoiEntry('import_pdfs', item)
            else:
                try:
                    DoiEntry('import_pdfs', item)
                except EntryExistsException as e:
                    logging.info(f"DOI already in database, skipping: {e}")
            total_count += 1
            if total_count % 10 == 0:
                logging.info(f"Done {total_count} out of {len(pdf_files)}")

    def download_dois_by_journal_size(self,
                                    start_year,
                                    end_year):
        sql = f'''SELECT journal_title,issn,count(doi)
                FROM dois
                where {self.sql_year_restriction(start_year, end_year)}
                and downloaded = False 
                GROUP BY journal_title
                ORDER BY COUNT(doi) ASC'''

        journals = DBConnection.execute_query(sql)
        for journal, issn, doi_count in journals:
            # journal = journal[0]
            # issn = journal[1]
            logging.info(f"Attempting downloads for journal: {journal}:{issn}")
            report = DatabaseReport(start_year, end_year, journal)
            logging.info("\n")
            logging.info(report.report(journal=journal, issn=issn, summary=False))
            self.download_dois(start_year, end_year, journal=journal, issn=issn)

    def _generate_select_sql(self, start_year, end_year, journal_issn, downloaded="FALSE"):
        select_dois = f"""select * from dois where downloaded={downloaded} """

        if start_year is not None and end_year is not None:
            select_dois += f""" and  {self.sql_year_restriction(start_year, end_year)}"""
        if journal_issn is not None:
            select_dois += f' and issn="{journal_issn}"'
        return select_dois

    def get_dois(self, start_year, end_year, journal_issn=None):
        sql = self._generate_select_sql(start_year, end_year, journal_issn, "TRUE")
        dois = DoiFactory(sql).dois
        return dois

    def get_doi(self, doi):
        sql = f"select * from dois where doi = '{doi}'"
        doi = DoiFactory(sql).dois
        if len(doi) != 1:
            raise FileNotFoundError(f"No such doi: {doi} or multiple results")
        return doi[0]

    def ensure_downloaded_has_pdf(self, start_year, end_year):
        dois = self.get_dois(start_year, end_year)
        for doi_entry in dois:
            doi_entry.check_file()
            doi_entry.update_database()

    # Ensures that all DOIs in the database have associated files
    # Download, if not.

    def download_dois(self,
                    start_year,
                    end_year,
                    journal=None,
                    issn=None):

        select_dois = self._generate_select_sql(start_year, end_year, issn)
        downloaders = Downloaders()

        doif = DoiFactory(select_dois)
        dois = doif.dois
        logging.info(f"SQL: {select_dois}")
        logging.info(f"  Pending download count: {len(dois)}")
        download_list = []
        for doi_entry in dois:
            if journal is None or doi_entry.issn == issn:
                download_list.append(doi_entry)

        downloaders.download_list(download_list)

    def is_downloaded(self, doi_entry):
        return doi_entry.downloaded

    def download_issn(self, issn, start_year, end_year):
        base_url = f"https://api.crossref.org/journals/{issn}/works?filter=from-pub-date:{start_year},until-pub-date:{end_year}&rows=1000&cursor="
        cursor = "*"
        done = False
        total_items_processed = 0
        total_results = 0
        logging.info(f"Processing issn:{issn}")
        while not done:
            try:
                cursor, total_results, items_processed = self._download_chunk(base_url, cursor, start_year)
                total_items_processed += items_processed
                logging.info("Continuing...")
            except ConnectionError:
                if total_items_processed >= total_results:
                    done = True
                    logging.info("Done.")
                else:
                    logging.info("retrying....")
            except RetriesExceededException as rex:
                logging.info(f"Retries exceeded: {rex}, aborting.")
                return

    def _handle_connection_error(self, retries, max_retries, url, cursor, start_year, e):
        logging.info(f"Connection error: {e}, retries: {retries}. Sleeping 60 and retrying.")
        time.sleep(60)
        if retries >= max_retries:
            raise RetriesExceededException(f"Retried {retries} times, aborting.")
        return self._download_chunk(url, cursor, start_year, retries)

    def _download_chunk(self, url, cursor, start_year, retries=0):
        max_retries = 3
        safe_cursor = urllib.parse.quote(cursor, safe="")
        try:
            results = self._get_url_(url + safe_cursor, self.headers)
        except ConnectionError as e:
            retries += 1
            return self._handle_connection_error(retries, max_retries, url, cursor, start_year, e)
        except requests.exceptions.ConnectionError as e:
            retries += 1
            return self._handle_connection_error(retries, max_retries, url, cursor, start_year, e)

        logging.info(f"Querying: {url + safe_cursor}")
        message = results['message']
        items = message['items']
        total_results = message['total-results']
        items_processed = 0
        for item in items:
            items_processed += 1
            # logging.info(f"Processing DOI: {item['DOI']}")
            type = item['type']
            if type == 'journal':
                CrossrefJournalEntry(item)
            elif type == "journal-article":
                try:
                    DoiEntry('download_chunk', item)
                except EntryExistsException as e:
                    # logging.warning(f"DOI already in database, skipping: {e}")
                    logging.info(".")
            else:
                # "journal-issue"
                # logging.info(f"got type: {type}")
                pass

        if len(items) == 0:
            logging.error("No items left.")
            raise ConnectionError()
        else:
            logging.info(f"Processed {len(items)} items")
        return message['next-cursor'], total_results, items_processed
