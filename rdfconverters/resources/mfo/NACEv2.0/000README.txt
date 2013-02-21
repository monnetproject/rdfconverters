
(C) Hans-Ulrich Krieger, DFKI-LT, Fri Dec 16 19:23:53 CET 2011

The NACE v2.0 ontology have been derived from NACE v1.0's N-triple file
by string manipulation.
Thus there was NO OWL-XML file that could be inspected by using, say,
Protege.
By using the Raptor RDF library, I was able to derive an OWL-XML Protege
project.

Basically, the instances (the industry sectors) from version 1 have been
assigned class status in version 2, so that nace:subSectorOf got replaced
by rdfs:subClassOf over these new classes.
The English, German, and Italian description of the industry sectors
still uses rdfs:label.
The original datatype properties nace:hasCode and nace:hasLevel are
defined to be OWL annotation properties on the industry classes.

There exists a "synthetical" superclass nace:IndustrySector whose direct
subclasses are the top-level NACE sectors nace:nace_A, ..., nace:nace_U.
