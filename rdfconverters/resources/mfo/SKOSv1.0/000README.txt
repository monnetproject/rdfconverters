
(C) Hans-Ulrich Krieger, DFKI-LT

The SKOS ontology (our own version) is of species OWL-Full,
since we let certain SKOS properties talk about classes (just
as rdfs:subClassOf does) instead of instances of classes.

Version 1.0 defines the basic properties we need at the moment
for our own (bidirectional) XEBR-to-XBRL mapping:
  * exactMatch
  * closeMatch
  * relatedMatch
  * broadMatch
  * narrowMatch

Since these properties are OWL object properties, we can assign
characteristics to them, saying, e.g., that they are transitive,
etc.
Both the domain and the range of these properties is owl:Class,
thus we do NOT make use of skos:Concept.

In addition, we include the following SKOS annotation properties:
  * prefLabel
  * altLabel
  * hiddenLabel

Since SKOS explicitly says that skos:broader and skos:narrower should
be read as the more general/more specific relation between two concepts,
we have skipped these two relations and require to use rdfs:subClassOf
instead.
