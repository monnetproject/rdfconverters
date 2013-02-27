from rdflib import Graph
import time
import sys
import rdfconverters.util
inp, out, format_in, format_out = sys.argv[1:]

t1 = int(round(time.time() * 1000))

with open(inp, 'r') as f:
    input_data = f.read()

graph_in = Graph().parse(data=input_data, format=format_in)
for k, v in rdfconverters.util.NS.items():
    graph_in.bind(k, v)
with open(out, 'wb') as f:
    f.write(graph_in.serialize(format=format_out))

t2 = int(round(time.time() * 1000))

print("Completed in %sms %s" % (t2-t1))
