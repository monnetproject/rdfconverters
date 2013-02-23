import unittest
import lxml._elementpath
from lxml import etree
from rdfconverters.dax2rdf.dax2rdf import Searcher, Fetcher, Scraper
from pprint import pprint as pp
from pkg_resources import resource_stream

class TestSearching(unittest.TestCase):

    def test_search_renewables_index(self):
        searcher = Searcher()
        results = searcher.search_index_constituents("DE000A0SM6L3")
        pp(results)
        print(len(results))
        self.assertTrue(results[0][0] == '3W Power S.A.')
        self.assertTrue(results[0][1] == 'GG00B39QCR01')
        self.assertEqual(len(results), 37)

class TestScraping(unittest.TestCase):
    def test_scraper(self):
        fetcher = Fetcher()
        scraper = Scraper(fetcher)

        result = scraper.scrape('GG00B39QCR01')


if __name__ == '__main__':
    unittest.main()
