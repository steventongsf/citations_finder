import unittest
from doi_entry import DoiFactory

class DoiEntryTest(unittest.TestCase):
    def test_query(self):
        select_dois = f"""select * from dois, unpaywall_downloader where downloaded=False 
                    and dois.doi = unpaywall_downloader.doi and unpaywall_downloader.open_url is not null"""
        #doif = DoiFactory(select_dois)
        #print(doif)