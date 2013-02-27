from rdflib import Graph
from rdfconverters.util import NS
from os.path import dirname, abspath
from pkg_resources import resource_stream

XEBR2XBRL_PATH = resource_stream('rdfconverters.resources', 'mfo/XEBR2XBRLv1.0/xebr2xbrl.n3')
x2x_graph = Graph()
x2x_graph.parse(XEBR2XBRL_PATH, format="n3")
for n in NS:
    x2x_graph.bind(n, NS[n])

class XBRL2XEBR:
    '''
    Creates a mapping from an XBRL taxonomy to an XEBR taxonomy, using
    the MFO XEBR2XBRL ontology.

    Give the namespace as a parameter to the constructor, e.g. "http://.../xbrl_es.owl#",

    then use get(gaap_concept_xml) to retrieve the XEBR concept, where gaap_concept_xml
    is the name of the tag used in the XBRL XML file, including the namespace prefix, e.g.
      get("pfs-07-b:ActivoCurriando") ----> "FixedAssets"
    '''

    def __rdf_name_to_xml_name(self, rdf_name):
        rdf_name = rdf_name.rsplit("#")[1]
        rdf_name = rdf_name.replace('_', ':', 1).replace(':has', ':', 1)
        return rdf_name

    def __init__(self, namespace):
        self.namespace = namespace
        self.mapping = self._generate_mapping()

    def _generate_mapping(self):
        mapping={}
        for s, _, o in x2x_graph.triples((None, NS['skos']['exactMatch'], None)):
            if s.format().startswith(self.namespace):
                s_xml = self.__rdf_name_to_xml_name(s)
                mapping[s_xml] = o.rsplit("#")[1]
        return mapping

    def get(self, gaap_concept_xml):
        if gaap_concept_xml in self.mapping:
            xebr_concept = self.mapping[gaap_concept_xml]
            return xebr_concept
        else:
            return None
