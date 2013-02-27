from rdflib import Graph, Namespace, URIRef, Literal
import xlrd
import re
from pprint import pprint as pp
from rdfconverters.util import NS
from rdfconverters import util
from pkg_resources import resource_string, resource_stream


'''
Generate XBRL2XEBR ontology from gaap files and the xEBR taxonomy Excel file (V7).
'''


class XEBRV7Concepts:
    def __init__(self, book):
        sheet = book.sheet_by_name('xEBR Concepts')
        header_count = 1
        concepts = sheet.col(11)[header_count:]
        types = sheet.col(12)[header_count:]
        self.map = {concept.value: type_.value for concept, type_ in zip(concepts, types) if len(concept.value)>0}

    def is_monetary(self, xebr_concept):
        return self.map[xebr_concept] == 'monetary'

    def contains(self, xebr_concept):
        return xebr_concept in self.map



class Mapper:
    def get_gaap_xebr_map(self): raise NotImplementedError()
    def get_prefixed(self, gaap_concept): raise NotImplementedError()
    @staticmethod
    def unprefix(concept):
        if not '_' in concept:
            return concept
        return concept.split('_', 1)[1]
class StandardXEBRV7Mapper(Mapper):
    def __init__(self, book):
        self.book = book
    def parse(self, sheet_name, gaap_col, match_col, xebr_col):
        GAAP_CONCEPT = 0; MATCH_TYPE = 1; XEBR_CONCEPT = 2
        sheet = self.book.sheet_by_name(sheet_name)
        rows = zip(sheet.col(gaap_col), sheet.col(match_col), sheet.col(xebr_col))
        # Remove non-exact matches
        rows = list(row for row in rows if row[MATCH_TYPE].value=='exact match')

        self.prefix_map = {Mapper.unprefix(row[GAAP_CONCEPT].value): row[GAAP_CONCEPT].value for row in rows}
        self.gaap_xebr_map = {
            Mapper.unprefix(row[GAAP_CONCEPT].value) : Mapper.unprefix(row[XEBR_CONCEPT].value)
            for row in rows
        }
    def get_gaap_xebr_map(self):
        return self.gaap_xebr_map
    def get_prefixed(self, gaap_concept):
        return self.prefix_map[gaap_concept]

class BEMapper(StandardXEBRV7Mapper):
    def __init__(self, xebr_xls):
        super().__init__(xebr_xls)
        self.parse('BEL', 1, 3, 4)

class ESMapper(StandardXEBRV7Mapper):
    def __init__(self, xebr_xls):
        super().__init__(xebr_xls)
        self.parse('SPA', 1, 3, 4)

class ITMapper(StandardXEBRV7Mapper):
    def __init__(self, xebr_xls):
        super().__init__(xebr_xls)
        self.parse('ITA', 0, 2, 4)









class GaapLabels:
    def __init__(self, gaap_graph, mapper, concept_namespaces, pref_label, alt_label):
        self.gaap_graph = gaap_graph
        self.mapper = mapper
        self.concept_namespaces = concept_namespaces
        self.pref_label = URIRef(pref_label)
        self.alt_label = URIRef(alt_label)

        self.labels = self.__generate_labels()

    def get_labels(self):
        return self.labels

    def __generate_labels(self):
        '''
        Get the labels used in a GAAP ontology file for concepts that have an exact xEBR match
        returns {
            'prefLabel': {gaapconcept: {lang: label}* }*,
            'altLabel':  {gaapconcept: {lang: label}* }*
        }
        '''
        results = {}
        for key, label in (('prefLabel', self.pref_label), ('altLabel', self.alt_label)):
            results[key] = {}
            for gaap, xebr in self.mapper.get_gaap_xebr_map().items():
                labels = []
                for concept_namespace in self.concept_namespaces:
                    ns = Namespace(concept_namespace)
                    labels += list(self.gaap_graph.objects(ns[gaap], label))
                if len(labels) > 0:
                    results[key][gaap] = {m.language: str(m) for m in labels}
                else:
                    print("WARNING: No label in GAAP for mapped concept %s/%s" % (xebr, gaap))
        return results

class BEGaapLabels(GaapLabels):
    def __init__(self, gaap_graph, gaap_xebr_map):
        super().__init__(
            gaap_graph, gaap_xebr_map,
            ['http://www.nbb.be/be/fr/pfs/ci/2011-04-01/'],
            'http://www.xbrl.org/2003/role/label',
            'http://www.xbrl.org/2003/role/verboseLabel')
class ITGaapLabels(GaapLabels):
    def __init__(self, gaap_graph, gaap_xebr_map):
        super().__init__(
            gaap_graph, gaap_xebr_map,
            ['http://www.infocamere.it/itnn/fr/itcc/ci/2011-01-04/'],
            'http://www.xbrl.org/2003/role/label',
            'http://www.xbrl.org/2003/role/verboseLabel')
class ESGaapLabels(GaapLabels):
    def __init__(self, gaap_graph, gaap_xebr_map):
        super().__init__(
            gaap_graph, gaap_xebr_map,
            ['http://www.icac.meh.es/es/fr/gaap/pgc07/comun-base/2009-01-01/',
                'http://www.icac.meh.es/es/fr/gaap/pgc07/normal/2009-01-01/'],
            'http://www.xbrl.org/2003/role/label',
            'http://www.xbrl.org/2003/role/verboseLabel')







class RDFConverter:
    def __init__(self, graph, xebr_concepts):
        self.graph = graph
        self.xebr_concepts = xebr_concepts

    def add_mappings_to_graph(self, mapper, gaap_labels, gaap_base):
        ns_gaap = Namespace(gaap_base)

        # See GaapLabels for structure
        for label_type in gaap_labels:
            for gaap_concept, labels in gaap_labels[label_type].items():
                # Add xEBR concept
                xebr_concept = mapper.get_gaap_xebr_map()[gaap_concept]
                if not self.xebr_concepts.contains(xebr_concept):
                    print("WARNING: Match in GAAP but no concept in xEBR: %s" % xebr_concept)
                    continue

                if self.xebr_concepts.is_monetary(xebr_concept):
                    xebr_concept = 'has' + xebr_concept

                # Add GAAP mapping
                gaap_concept = ns_gaap[mapper.get_prefixed(gaap_concept)]
                self.graph.add((gaap_concept, NS['skos']['exactMatch'], NS['xebr'][xebr_concept]))
                self.graph.add((gaap_concept, NS['owl']['equivalentProperty'], NS['xebr'][xebr_concept]))

                # Add labels
                for lang, label in labels.items():
                    clean_label = label.strip().replace('\n',' ')
                    self.graph.add((gaap_concept, NS['skos'][label_type], Literal(clean_label, lang=lang)))







def main():
    xls_file = resource_string('rdfconverters.resources', 'gaaps/xebrv7.xls')
    book = xlrd.open_workbook(file_contents=xls_file)

    xebr_concepts = XEBRV7Concepts(book)
    # RDF output graph
    xebr2xbrl = Graph()
    for key, ns in NS.items():
        xebr2xbrl.bind(key, ns)
    rdf_converter = RDFConverter(xebr2xbrl, xebr_concepts)

    def map_gaap(clazz_mapper, f, clazz_labels, base):
        mapper = clazz_mapper(book)
        graph = Graph().parse(f, format='n3')
        labels = clazz_labels(graph, mapper).get_labels()
        rdf_converter.add_mappings_to_graph(mapper, labels, base)


    f = resource_stream('rdfconverters.resources', 'gaaps/it.n3')
    map_gaap(ITMapper, f, ITGaapLabels, 'http://www.dfki.de/lt/xbrl_it.owl#')

    f = resource_stream('rdfconverters.resources', 'gaaps/pgc.n3')
    map_gaap(ESMapper, f, ESGaapLabels, 'http://www.dfki.de/lt/xbrl_es.owl#')

    f = resource_stream('rdfconverters.resources', 'gaaps/be.n3')
    map_gaap(BEMapper, f, BEGaapLabels, 'http://www.dfki.de/lt/xbrl_be.owl#')


    util.write_graph(xebr2xbrl, '/tmp/xebr2xbrl.n3')

if __name__ == '__main__':
    main()
