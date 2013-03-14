from rdflib import BNode, Literal, Graph, URIRef
from rdfconverters.util import NS
from pkg_resources import resource_string, resource_stream

f = resource_string('rdfconverters.resources', 'isin_companyid_map.txt').decode('utf-8')
isin_companyid_map = {}
for entry in f.split('\n'):
    if len(entry.strip()) > 0:
        isin, companyid = entry.split(' ')
        isin_companyid_map[isin] = companyid

def companyid(isin):
    if isin in isin_companyid_map.keys():
        return isin_companyid_map[isin]
    return None


IF_PATH = resource_stream('rdfconverters.resources', 'mfo/IFv1.3/if.n3')
if_graph = Graph()
if_graph.parse(IF_PATH, format="n3")
for n in NS:
    if_graph.bind(n, NS[n])

def country_from_name(name, lang='en'):
    return if_graph.value(predicate=NS['rdfs']['label'], object=Literal(name, lang=lang))



class CPNodeBuilder:
    '''Helps to create bnodes for CompanyProfile ontology'''

    def __init__(self, graph, id_node):
        self.g = graph
        self.node = BNode()
        self.id_node = id_node

    def structured(self):
        self.g.add((self.node, NS['rdf']['type'], NS['cp']['Structured']))
        return self

    def unstructured(self, *annotations):
        self.g.add((self.node, NS['rdf']['type'], NS['cp']['Unstructured']))
        for annotation in annotations:
            self.g.add((self.node, NS['cp']['annotation'], Literal(annotation)))
        return self

    def sector_value(self, prop, value):
        self.g.add((self.id_node, NS['cp'][prop], self.node))
        self.g.add((self.node, NS['rdf']['type'], NS['cp']['SectorValue']))
        self.g.add((self.node, NS['cp']['sectorValue'], value))

    def string_value(self, prop, value):
        self.g.add((self.id_node, NS['cp'][prop], self.node))
        self.g.add((self.node, NS['rdf']['type'], NS['cp']['StringValue']))
        self.g.add((self.node, NS['cp']['stringValue'], Literal(value)))
