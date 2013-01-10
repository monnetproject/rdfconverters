from rdflib import Graph
from rdflib.compare import to_isomorphic, graph_diff
import sys

if len(sys.argv)>=3:
   F1 = sys.argv[1]
   F2= sys.argv[2] 
else:
   F1 = "/home/barry/Downloads/instance.ttl"
   F2 = "/home/barry/Downloads/t2.ttl"
g1 = Graph()
g1.parse(F1, format="turtle")

g2 = Graph()
g2.parse(F2, format="turtle")

iso1 = to_isomorphic(g1)
iso2 = to_isomorphic(g2)

in_both, in_first, in_second = graph_diff(iso1, iso2)

if len(sys.argv)==4:
   print(in_first.serialize(format="n3").decode('utf-8'))
else:
   print(in_second.serialize(format="n3").decode('utf-8'))

