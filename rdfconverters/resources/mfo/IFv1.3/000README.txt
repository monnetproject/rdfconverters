
(C) Hans-Ulrich Krieger, DFKI-LT

Contrary to MFO v1.0 which makes the DAX ontology "responsible" for
interfacing the sub-ontologies, we have decided to come up with a
separate "interface" ontology IF (v1.0) in MFO v2.0 which is solely
responsible for bringing the 7 sub-ontologies together.

The reason for collecting the interface information in a single file
makes the sub-ontologies independent of/decouple from each other, and
furthermore have a single point, where everything gets located, making
the complete ontology more perspicuous.

Basically, IF identifies dax:Company, en:Company, nace:IndustrySector,
and icb:ICB, using owl:equivalentClass.
IF, furthermore, identifies some basic properties from DAX and EN, such
as dax:portrait and en:activity, using owl:equivalentProperty.
IF also defines the range of en:cfi to be of class cfi:CFI.
In addition, IF relates the range of dax:hasReport to xebr:Report, and
defines xebr:Report to be a subtype of dc:Resource, thus letting
xebr:Report inherit some of the basic properties from Dublin Core.

CHANGES in Version 1.1
----------------------
  * A new property if:origin has been added that shows where the company
    information comes from, plus a subtype hierarchy over stock exchange
    places.
  * A new property if:hasReport has been added (originally defined in
    the DAX namespace) which connects {dax:Company, nace:IndustrySector,
    en:Company, icb:ICB} with xebr:Report.

CHANGES in Version 1.2
----------------------
  * The original "N-triple" file has been made fully compatible with the
    N-triple specification by using solely long namespace descriptions.
  * From the updated N-triple file, I have generated an OWL-XML version
    that can be viewed more pleasantly, using Protege.
    This file contains some redundant/useless information in order to
    inform Protege about the relationship of classes and properties with
    the built-in classes and properties from RDF(S) and OWL;
    e.g., that en:Company is an instance of owl:Class (otherwise,
    en:Company would not a subclass of owl:Thing in case the IF ontology
    is viewed alone).
    Note that equivalent propertiesare NOT depicted in the Protege view.

CHANGES in Version 1.3
----------------------
  * Labels have been added to the singleton instances that are used by
    if:origin.