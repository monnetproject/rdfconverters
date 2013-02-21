	
(C) Hans-Ulrich Krieger, DFKI-LT

The Industry Classification Benchmark ontology, version 1 (ICB v1.0)
has been derived from the ICB taxonomy which can be found on the ICB
website of FTSE.

ICB is a four-level industry sector classification, where each sector
comes with an NL-like sector name in 11 languages and a NL definition
of the leaf sector (level 4), no further subclasses), again in 11
languages.

I have used the annotation property rdfs:label to attach the sector
name to a class and have defined a new annotation property in the RDFS
namespace, called rdfs:definition, in order to store the associated
definition of the leaf industry sectors

The 10 top-level industry sectors of ICB have been made subclasses of
a new synthetical superclass, calles ICB.

Version 1 of ICB is currently shipped with the English description.


CHANGES in Version 1.1
----------------------
German & Spanish labels and definitions have been added by Dagmar
Gromann (WU Wien) for all classes.
