from rdflib import BNode, Literal
from rdfconverters.util import NS

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
