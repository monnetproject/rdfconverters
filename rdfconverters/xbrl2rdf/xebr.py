from rdflib import Graph
from rdfconverters.util import NS
from pkg_resources import resource_stream

XEBR_PATH = resource_stream('rdfconverters.resources', 'mfo/XEBRv7.0/xebr.n3')
graph = Graph()
graph.parse(XEBR_PATH, format="n3")
for n in NS:
    graph.bind(n, NS[n])
