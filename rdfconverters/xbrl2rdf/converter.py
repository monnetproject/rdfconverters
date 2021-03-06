from rdfconverters.xbrl2rdf.traverser import XEBRConceptTraverser
from rdfconverters.xbrl2rdf import xebr
from rdfconverters.xbrl2rdf.metrics import Metrics
from rdflib import Graph, URIRef, Literal, XSD, BNode
import re
from rdfconverters.util import NS


class RDFConverter:
    def __init__(self):
        self.traverser = XEBRConceptTraverser()

    def _abbreviate(self, s):
        return re.sub('[^A-Z]', r'', s).lower()

    def _write_metrics(self, g, rep, identifier, filing):
        metrics = Metrics(filing['items'])

        for concept_name, function in metrics.get_metrics().items():
            concept = NS['xebr'][concept_name]
            datatype = xebr.graph.value(subject=concept, predicate=NS['rdfs']['range'])
            assert datatype is not None
            value = function()

            if value is not None:
                metric_id = NS['xebr']["%s_%s" % (concept_name, identifier)]
                g.add((metric_id, NS['xebr'][concept_name], Literal(value, datatype=datatype)))
                g.add((rep, NS['xebr']['hasMetric'], metric_id))

    def convert(self, xbrl_instance):
        g = Graph()
        for n in NS:
            g.bind(n, NS[n])

        for filing in xbrl_instance.get_filings_list():
            identifier = "%s_%s" % ( filing['metadata']['id'], filing['metadata']['end'] )

            # Add report instance to graph, with start/end metadata
            rep = NS['xebr']['rep_'+identifier]
            metadata = filing['metadata']
            g.add((rep, NS['rdf']['type'], NS['xebr']['Report']))
            g.add((rep, NS['xebr']['sourceTaxonomy'], URIRef(metadata['taxonomy'])))
            g.add((rep, NS['xebr']['start'], Literal(metadata['start'],datatype=XSD.date)))
            g.add((rep, NS['xebr']['end'], Literal(metadata['end'],datatype=XSD.date)))
            if 'source' in metadata:
                datatype = metadata['source'][1]
                g.add((rep, NS['dc']['source'], Literal(metadata['source'][0],datatype=datatype)))

            # Metrics
            self._write_metrics(g, rep, identifier, filing)

            # Traverse concepts and add to graph
            for report_type in self.traverser.report_type_iterator():
                for report in self.traverser.report_iterator(report_type):
                    node_belongsTo = NS['xebr']["%s_%s" % (self._abbreviate(report), identifier)]
                    empty_report=True
                    for abstract_concept, concepts, depth in self.traverser.concept_iterator(report):
                        concepts_in_filing = set(filing['items']) & set(concepts.keys())

                        # Add concepts to graph
                        if len(concepts_in_filing) > 0:
                            empty_report=False
                            ab = NS['xebr']["%s_%s" % (self._abbreviate(abstract_concept), identifier)]

                            # Add abstract_concept and report relationships
                            g.add((ab, NS['rdf']['type'], NS['xebr'][abstract_concept]))
                            g.add((ab, NS['xebr']['belongsTo'], node_belongsTo))

                            # Add all has* properties and values
                            for concept in concepts_in_filing:
                                value = filing['items'][concept]
                                if value is not None:
                                    if isinstance(value, URIRef):
                                        g.add( (ab, NS['xebr'][concept], value) )
                                    else:
                                        # Treat strings as plain literals
                                        if str(concepts[concept]) == "http://www.w3.org/2001/XMLSchema#string":
                                            datatype=None
                                        else:
                                            datatype=concepts[concept]
                                        g.add( (ab, NS['xebr'][concept], Literal(value, datatype=datatype)) )

                    # Only add metadata for the report if it has values for associated
                    # concepts below it in the tree
                    if not empty_report:
                        g.add((node_belongsTo, NS['rdf']['type'], NS['xebr'][report]))
                        g.add((node_belongsTo, NS['xebr']['belongsTo'], node_belongsTo))
                        g.add((rep, NS['xebr']["has"+report_type], node_belongsTo))

        return g
