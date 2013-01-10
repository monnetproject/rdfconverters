from rdflib import Namespace, Graph
from util import RDFUtil

class XEBRConceptTraverser:
    '''
    Iterators for traversing the tree of reports in the XEBR ontology of the MFO.

    See the "xEBR Matrix" sheet in "xEBR v7.0-Financial Figures-rdf-mappings.xls" file for the
    report taxonomy. Run `cat notes/structure` for the MFO version of that excel sheet.
    '''
    XEBR_PATH = 'schemas/xebr.n3'
    NS = {
        'rdf': Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        'rdfs': Namespace("http://www.w3.org/2000/01/rdf-schema#"),
        'xebr': Namespace('http://www.dfki.de/lt/xebr.owl#'),
        'skos': Namespace('http://www.dfki.de/lt/skos.owl#')
    }

    def __init__(self):
        # Load XEBR schema
        self.gx = Graph()
        self.gx.parse(self.XEBR_PATH, format="n3")
        for n in self.NS:
            self.gx.bind(n, self.NS[n])

    def all_report_types(self):
        '''Query XEBR ontology for all report types'''
        report = self.NS['xebr']['Report']
        domain = self.NS['rdfs']['domain']
        range_ = self.NS['rdfs']['range']
        reports=[]
        for s in self.gx.subjects(domain, report):
            for o in self.gx.objects(s, range_):
                reports.append(o)
        return reports

    def report_type_iterator(self):
        for report_type in self.all_report_types():
            yield RDFUtil.uri_to_concept(report_type)

    def report_iterator(self, report_type):
        partOf = self.NS['xebr']['partOf']
        for report in self.gx.subjects(partOf, self.NS['xebr'][report_type]):
            yield RDFUtil.uri_to_concept(report)

    def _generate_concepts_dict(self, abstract_concept):
        '''
        Given an XEBR abstract concept, returns a dict of has* concepts as keys with their data type
        as values.
        '''
        domain = self.NS['rdfs']['domain']
        haslist = [s for s in self.gx.subjects(domain, self.NS['xebr'][abstract_concept])]
        # Map has* properties to data type
        has = {}
        for s ,_, t in self.gx.triples((None, self.NS['rdfs']['range'], None)):
            if s in haslist:
                has[ RDFUtil.uri_to_concept(s) ] = t
        return has

    def concept_iterator(self, abstract_concept, depth=0):
        '''
        Recursively iterate through the XEBR concept tree, returning a tuple containing
        each abstract concept, its list of has* concepts, and its depth in the tree.
        '''
        partOf = self.NS['xebr']['partOf']

        concepts = self._generate_concepts_dict(abstract_concept)
        yield (abstract_concept, concepts, depth)

        for abstract_concept_child_url in self.gx.subjects(partOf, self.NS['xebr'][abstract_concept]):
            abstract_concept = RDFUtil.uri_to_concept(abstract_concept_child_url)

            # Yield recursively
            for values in self.concept_iterator(abstract_concept, depth+1):
                yield values

if __name__ == '__main__':
    x = XEBRConceptTraverser()
    for report_type in x.report_type_iterator():
        print(report_type)
        for report in x.report_iterator(report_type):
            for abstract_concept, concepts, depth in x.concept_iterator(report_type):
                print(abstract_concept, depth)
                for c in concepts:
                    print("   " + c)
    '''
    x = XEBRConceptTraverser()
    for report_type in x.report_type_iterator():
        for abstract_concept, concepts, depth in x.concept_iterator(report_type):
            print(report_type, abstract_concept, depth)
            for c in concepts:
                print("   " + c)
    '''
