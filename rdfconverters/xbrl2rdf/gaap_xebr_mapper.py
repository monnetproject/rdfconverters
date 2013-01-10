from rdflib import Graph, Namespace
from util import RDFUtil

class XBRL2XEBR:
    '''
    Creates a mapping from an XBRL taxonomy to an XEBR taxonomy, using
    the MFO XEBR2XBRL ontology.

    Give the namespace as a parameter to the constructor, e.g. "http://.../xbrl_es.owl#",

    then use get(gaap_concept_xml) to retrieve the XEBR concept, where gaap_concept_xml
    is the name of the tag used in the XBRL XML file, including the namespace prefix, e.g.
      get("pfs-07-b:ActivoCurriando") ----> "FixedAssets"
    '''
    XEBR2XBRL_PATH = 'schemas/xebr2xbrl.n3'
    NS = {
        'skos': Namespace('http://www.dfki.de/lt/skos.owl#')
    }

    def __init__(self, namespace):
        # Load XEBR2XBRL schema
        self.namespace = namespace
        self.g = Graph()
        self.g.parse(self.XEBR2XBRL_PATH, format="n3")
        for n in self.NS:
            self.g.bind(n, self.NS[n])
        self.mapping = self._generate_mapping()

    def _generate_mapping(self):
        mapping={}
        for s, _, o in self.g.triples((None, self.NS['skos']['exactMatch'], None)):
            if s.format().startswith(self.namespace):
                s_xml = RDFUtil.rdf_name_to_xml_name(s)
                mapping[s_xml] = RDFUtil.uri_to_concept(o)
        return mapping

    def get(self, gaap_concept_xml):
        if gaap_concept_xml in self.mapping:
            xebr_concept = self.mapping[gaap_concept_xml]
            return xebr_concept
        else:
            return None
