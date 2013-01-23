import unittest
from lxml import etree
from rdfconverters.xbrl2rdf.xbrl import XBRLFactory, XBRLBelgium, XBRLSpainPGC
from pprint import pprint as pp
from pkg_resources import resource_stream

def get_report_tree(report):
    reportfile = resource_stream(__name__, 'fixtures/'+report)
    tree = etree.parse(reportfile)
    return tree


class TestXBRLAutoDetect(unittest.TestCase):

    def test_be(self):
        self.report = XBRLFactory.from_autodetected(get_report_tree('bereport.xbrl'))
        self.assertTrue(isinstance(self.report, XBRLBelgium))

    def test_es_pgc(self):
        self.report = XBRLFactory.from_autodetected(get_report_tree('espgcreport.xbrl'))
        self.assertTrue(isinstance(self.report, XBRLSpainPGC))

class TestXBRLBelgiumParsing(unittest.TestCase):

    def setUp(self):
        self.report = XBRLFactory.from_autodetected(get_report_tree('bereport.xbrl'))

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


class TestXBRLReport(unittest.TestCase):

    def setUp(self):
        self.report = XBRLFactory.from_autodetected(get_report_tree('bereport.xbrl'))

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
