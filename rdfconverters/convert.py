from rdflib import Graph
import sys
import rdfconverters.util
inp, out, format_in, format_out = sys.argv[1:]

graph_in = Graph().parse(inp, format=format_in)
for k, v in rdfconverters.util.NS.items():
    graph_in.bind(k, v)
with open(out, 'wb') as f:
    f.write(graph_in.serialize(format=format_out))
