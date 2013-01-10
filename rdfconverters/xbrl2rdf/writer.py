from traverser import XEBRConceptTraverser
from rdflib import Graph, URIRef, Namespace, Literal, XSD
import re

class RDFWriter:
    def _abbreviate(self, s):
        return re.sub('[^A-Z]', r'', s).lower()

    def __init__(self, xbrl_instance):
        self.xbrl_instance = xbrl_instance

        self.NS = {
            'rdf': Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            'dc': Namespace("http://www.dfki.de/lt/dc.owl#"),
            'xebr': Namespace('http://www.dfki.de/lt/xebr.owl#'),
            'xmls': Namespace('http://www.w3.org/2001/XMLSchema#'),
        }

        self.g = Graph()
        for n in self.NS:
            self.g.bind(n, self.NS[n])

    def generate_rdf(self, format="n3"):
        for filing in self.xbrl_instance.get_filings_list():
            identifier = "%s_%s" % ( filing['metadata']['id'], filing['metadata']['end'] )

            # Add report instance to graph, with start/end metadata
            rep = URIRef('rep_'+identifier)
            metadata = filing['metadata']
            self.g.add((rep, self.NS['rdf']['type'], self.NS['xebr']['Report']))
            self.g.add((rep, self.NS['xebr']['start'], Literal(metadata['start'],datatype=XSD.date)))
            self.g.add((rep, self.NS['xebr']['end'], Literal(metadata['end'],datatype=XSD.date)))
            if 'source' in metadata:
                datatype = metadata['source'][1]
                self.g.add((rep, self.NS['dc']['source'], Literal(metadata['source'][0],datatype=datatype)))

            # Traverse concepts and add to graph
            x = XEBRConceptTraverser()
            for report_type in x.report_type_iterator():
                for report in x.report_iterator(report_type):
                    node_belongsTo = URIRef("%s_%s" % (self._abbreviate(report), identifier))
                    empty_report=True
                    for abstract_concept, concepts, depth in x.concept_iterator(report):
                        concepts_in_filing = set(filing['items']) & set(concepts.keys())

                        # Add concepts to graph
                        if len(concepts_in_filing) > 0:
                            empty_report=False
                            ab = URIRef("%s_%s" % (self._abbreviate(abstract_concept), identifier))

                            # Add abstract_concept and report relationships
                            self.g.add((ab, self.NS['rdf']['type'], self.NS['xebr'][abstract_concept]))
                            self.g.add((ab, self.NS['xebr']['belongsTo'], node_belongsTo))

                            # Add all has* properties and values
                            for concept in concepts_in_filing:
                                value = filing['items'][concept]
                                if value is not None:
                                    # Don't put datatype on strings
                                    if concepts[concept] == URIRef("http://www.w3.org/2001/XMLSchema#string"):
                                        datatype=None
                                    else:
                                        datatype=concepts[concept]
                                    self.g.add( (ab, self.NS['xebr'][concept], Literal(value, datatype=datatype)) )

                    # Only add metadata for the report if it has values for associated
                    # concepts below it in the tree
                    if not empty_report:
                        self.g.add((node_belongsTo, self.NS['rdf']['type'], self.NS['xebr'][report]))
                        self.g.add((node_belongsTo, self.NS['xebr']['belongsTo'], node_belongsTo))
                        self.g.add((rep, self.NS['xebr']["has"+report_type], node_belongsTo))

        output = self.g.serialize(format=format)
        return output.decode('utf-8')
