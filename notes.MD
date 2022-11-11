notes.MD

__additional packages__
pytest
pytest-html

__Refactoring comments__

* Use dependency injection with database access to improve ability to write unit tests
* Some configuration references are hard-coded and should be extracted to ini file


__Typical Workflow (guess)__
* Stage 1
    * Create database
    * Create tables in local Sqlite3 database (the main.py routine doesn't create everything but the DoiDatabase class does)
* Stage 2
    * Get journals from configuration
    * For each journal, call to journal_finder.addJournals
        * get jorunals from journals.tsv
        * go to gbif and see if there are any new journals
        * for each jorunal, get cross reference by doi
        * if journal not in dict, look up by title
    * write any missiong issn's to journals.tsv
* Stage 3
    * run downloaders.  Single downloader: UnpaywallDownloader
* Stage 4
    * DoiDatabase
        * insert into db.journals
        * download from api.  depending on type: journal => db.crossref_journal_data, journal-article=>db.dois
        * insert/update db.journals
    * import PDFs
        * for each pdf
        * get crossref.org metadata and add/update Doi record
* Stage 5
    * DoiDatabase again
* Stage 6
    * query database for all journal records and
        * download issn
        * updatedb.journals record

__Isolated Execution__
* empty database
* refresh journals.tsv
* download crossrefs
* run unpaywall downloader (review pdfs downloaded)
* scan pdfs
* optinally validate
* copy out?
