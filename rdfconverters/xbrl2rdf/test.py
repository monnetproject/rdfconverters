import unittest
from xbrl import *
from pprint import pprint
from ja import XEBRConceptIterator

class TestXBRLInstance(unittest.TestCase):

    def setUp(self):
        xbrli="/home/barry/code/monnet-wp1/data/xbrl/reports/es-gaap/fersa-20090101/xml/Fersa ES0136463017_2009.xbrl"
        self.x = XBRLInstance(xbrli)

    def test_concept_iterator(self):
        '''Sanity test concept iterator to ensure it returns data in the format we expect.'''
        for top_parent, parent, has in XEBRConceptIterator('KeyBalanceSheetFiguresReport'):
            if parent == 'OperatingChargesPresentation':
                self.assertEquals(top_parent.format(), 'http://www.dfki.de/lt/xebr.owl#IncomeStatementPresentation')
                x = ['hasWagesAndSalaries', 'hasOtherOperatingCharges', 'hasPensionsAndSimilarCommitments',
                      'hasRawMaterialsAndConsumables', 'hasOperatingChargesTotal']
                # Ensure lists are the same (even if order is different)
                self.assertEquals(set(has), set(x))
                break
        else:
            self.fail("Concept not found")


    def test_contexts(self):
        g = GAAPToXBRLTransformer(self.x)
        pprint (g.xbrl_map, depth=3)

if __name__ == '__main__':
    unittest.main()
