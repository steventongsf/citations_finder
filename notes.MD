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
        * a
