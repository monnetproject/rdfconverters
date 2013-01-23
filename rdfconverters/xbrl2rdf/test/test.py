import unittest
import lxml._elementpath
from lxml import etree
from rdfconverters.xbrl2rdf.xbrl import XBRLFactory, XBRLBelgium, XBRLSpainPGC, XBRLSpainCNMV
from pprint import pprint as pp
from pkg_resources import resource_stream

BE_REPORT = 'bereport.xbrl'
ES_PGC_REPORT = 'espgcreport.xbrl'
ES_CNMV_REPORT = 'cnmvreport.xbrl'

def get_fixture_file(report):
    return resource_stream(__name__, 'fixtures/'+report)

class TestXBRLAutoDetect(unittest.TestCase):

    def test_be(self):
        fixture_file = get_fixture_file(BE_REPORT)
        report = XBRLFactory.from_autodetected(etree.parse(fixture_file))
        self.assertTrue(isinstance(report, XBRLBelgium))

        fixture_file.close()

    def test_es_pgc(self):
        fixture_file = get_fixture_file(ES_PGC_REPORT)
        report = XBRLFactory.from_autodetected(etree.parse(fixture_file))
        self.assertTrue(isinstance(report, XBRLSpainPGC))
        fixture_file.close()

    def test_es_cnmv(self):
        fixture_file = get_fixture_file(ES_CNMV_REPORT)
        report = XBRLFactory.from_autodetected(etree.parse(fixture_file))
        self.assertTrue(isinstance(report, XBRLSpainCNMV))
        fixture_file.close()


class TestXBRLBelgiumParsing(unittest.TestCase):

    def setUp(self):
        self.fixture_file = get_fixture_file(BE_REPORT)
        self.report = XBRLFactory.from_autodetected(etree.parse(self.fixture_file))

    def tearDown(self):
        self.fixture_file.close()

    def test_filings_items(self):
        self.report.parse_filings()
        filings = self.report.get_filings_list()
        for filing in filings:
            if filing['metadata']['is_previous'] == True:
                self.assertEqual(filing['items']['hasFixedAssetsTotal'], '1330884.57EUR')
            else:
                self.assertEqual(filing['items']['hasFixedAssetsTotal'], '1466182.35EUR')

    def test_parsing_start_and_end_dates(self):
        self.report.parse_filings()
        filings = self.report.get_filings_list()
        self.assertEqual(len(filings), 2)

        for filing in filings:
            if filing['metadata']['is_previous'] == True:
                self.assertEqual(filing['metadata']['start'], '2008-01-01')
                self.assertEqual(filing['metadata']['end'], '2008-12-31')
            else:
                self.assertEqual(filing['metadata']['start'], '2009-01-01')
                self.assertEqual(filing['metadata']['end'], '2009-12-31')


class TestXBRLSpainCNMVParsing(unittest.TestCase):

    def setUp(self):
        self.fixture_file = get_fixture_file(ES_CNMV_REPORT)
        self.report = XBRLFactory.from_autodetected(etree.parse(self.fixture_file))

    def tearDown(self):
        self.fixture_file.close()

    def test_filings_items(self):
        self.report.parse_filings()
        filings = self.report.get_filings_list()
        for filing in filings:
            # Check ActivoNoCorrienteNacional mapping
            if filing['metadata']['is_previous'] == True:
                self.assertEqual(filing['items']['hasFixedAssetsTotal'], '287635000EUR')
            else:
                self.assertEqual(filing['items']['hasFixedAssetsTotal'], '299837000EUR')

    def test_parsing_start_and_end_dates(self):
        self.report.parse_filings()
        filings = self.report.get_filings_list()
        self.assertEqual(len(filings), 2)

        for filing in filings:
            if filing['metadata']['is_previous'] == True:
                self.assertEqual(filing['metadata']['start'], '2008-01-01')
                self.assertEqual(filing['metadata']['end'], '2008-12-31')
            else:
                self.assertEqual(filing['metadata']['start'], '2009-01-01')
                self.assertEqual(filing['metadata']['end'], '2009-12-31')



class TestXBRLReport(unittest.TestCase):

    def setUp(self):
        self.fixture_file = get_fixture_file(BE_REPORT)
        self.report = XBRLFactory.from_autodetected(etree.parse(self.fixture_file))

    def tearDown(self):
        self.fixture_file.close()

    def test_contexts(self):
        self.assertTrue('CurrentInstant' in self.report.contexts)
        self.assertTrue(self.report.contexts['CurrentInstant']['instant'] == '2009-12-31')
        self.assertTrue(self.report.contexts['PrecedingDuration']['start'] == '2008-01-01')

    def test_units(self):
        self.assertEqual(self.report.units['U-Pure'], '')
        self.assertEqual(self.report.units['U-Shares'], '')
        self.assertEqual(self.report.units['EUR'], 'EUR')

    def test_financial_items(self):
        self.assertEqual(self.report.items['CurrentInstant']['pfs:FixedAssets'], '1466182.35EUR')

    def test_financial_item_with_decimals(self):
        # Value in report is 19795000 with @decimals='-3'
        self.assertEqual(self.report.items['CurrentInstant']['pfs:FormationExpenses'], '197955EUR')

    def test_get_contexts_by_end(self):
        by_end = self.report._get_contexts_by_end()
        self.assertEqual(sorted(by_end['2008-12-31']), ['PrecedingDuration', 'PrecedingInstant'])
        self.assertEqual(sorted(by_end['2009-12-31']), ['CurrentDuration', 'CurrentInstant'])

    def test_expanded_xml_tag_to_prefixed(self):
        prefixed = self.report._expanded_xml_tag_to_prefixed('{http://www.xbrl.org/2003/iso4217}EUR')
        self.assertEqual(prefixed, 'iso4217:EUR')

    def test_items_in_contexts(self):
        items = self.report._items_in_contexts('CurrentDuration', 'PrecedingInstant')
        # Item from CurrentDuration context
        self.assertEqual(items['pfs:MiscellaneousOperatingCharges'], '10800.32EUR')
        # Item from PrecedingInstant context
        self.assertEqual(items['pfs:ResearchDevelopmentCostsAcquisitionValue'], '47889.52EUR')


if __name__ == '__main__':
    unittest.main()
