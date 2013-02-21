
(C) Hans-Ulrich Krieger, DFKI-LT

The time ontology, to be more specific, the property types
  * time:SynchronicProperty
  * time:DiachronicProperty
have already been used in the DAX and EN ontology in order to cross-classify
properties, whether being synchronic or diachronic (besides the usual other
property characteristics in OWL, owl:FunctionalProperty, owl:SymmetricProperty,
owl:ObjectProperty, owl:DatatypeProperty, etc.).

CHANGES in Version 1.1
----------------------
From the small N-triple file, we have generated a Protege project, so that
time:SynchronicProperty and time:DiachronicProperty will be displayed as
subclasses of rdf:Property.
The N-triple file now correctly uses long namespace prefixes.
