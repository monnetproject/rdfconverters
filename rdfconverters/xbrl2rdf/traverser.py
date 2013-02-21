from rdflib import Namespace, Graph
from pkg_resources import resource_stream
from rdfconverters.util import NS

class XEBRConceptTraverser:
    '''
    Iterators for traversing the tree of reports in the XEBR ontology of the MFO.

    See the "xEBR Matrix" sheet in "xEBR v7.0-Financial Figures-rdf-mappings.xls" file for the
    report taxonomy. Run `cat notes/structure` for the MFO version of that excel sheet.
    '''
    XEBR_PATH = resource_stream(__name__, '/schemas/xebr_v1.2.n3')

    def __init__(self):
        # Load XEBR schema
        self.gx = Graph()
        self.gx.parse(self.XEBR_PATH, format="n3")
        for n in NS:
            self.gx.bind(n, NS[n])

        # This is an instance variable for optimisation reasons
        self.range_triples = list(
            (self.__uri_to_concept(s), t) for s, _, t in self.gx.triples((None, NS['rdfs']['range'], None))
        )


    def __uri_to_concept(self, uri):
        return uri.rsplit("#")[1]

    def all_report_types(self):
        '''Query XEBR ontology for all report types'''
        report = NS['xebr']['Report']
        domain = NS['rdfs']['domain']
        range_ = NS['rdfs']['range']
        reports=[]
        for s in self.gx.subjects(domain, report):
            for o in self.gx.objects(s, range_):
                reports.append(o)
        return reports

    def report_type_iterator(self):
        for report_type in self.all_report_types():
            yield self.__uri_to_concept(report_type)

    def report_iterator(self, report_type):
        partOf = NS['xebr']['partOf']
        for report in self.gx.subjects(partOf, NS['xebr'][report_type]):
            yield self.__uri_to_concept(report)

    def _generate_concepts_dict(self, abstract_concept):
        '''
        Given an XEBR abstract concept, returns a dict of has* concepts as keys with their data type
        as values.
        '''
        domain = NS['rdfs']['domain']
        haslist = set(self.__uri_to_concept(s) for s in self.gx.subjects(domain, NS['xebr'][abstract_concept]))
        # Map has* properties to data type
        has = {}

        for s, t in self.range_triples:
            if s in haslist:
                has[ s ] = t
        return has

    def concept_iterator(self, abstract_concept, depth=0):
        '''
        Recursively iterate through the XEBR concept tree, returning a tuple containing
        each abstract concept, its list of has* concepts, and its depth in the tree.
        '''
        partOf = NS['xebr']['partOf']

        concepts = self._generate_concepts_dict(abstract_concept)
        yield (abstract_concept, concepts, depth)

        for abstract_concept_child_url in self.gx.subjects(partOf, NS['xebr'][abstract_concept]):
            abstract_concept = self.__uri_to_concept(abstract_concept_child_url)

            # Yield recursively
            for values in self.concept_iterator(abstract_concept, depth+1):
                yield values

