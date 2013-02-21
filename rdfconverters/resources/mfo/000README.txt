
(C) Hans-Ulrich Krieger, Tue Apr  3 14:48:22 CEST 2012

The MONNET Financial Ontology (MFO), version 3.0 consists of the following sub-ontologies:
  * CFI v2.0
  * DAX v2.4
  * DC v1.0 
  * EN v1.1
  * ICB v1.1
  * IF v1.3 (updated)
  * NACE v2.0
  * SKOS v1.0 (new)
  * TIME v1.1
  * XEBR2XBRLv1.0 (new)
  * XEBR v1.2 (updated)

MFO v2.1 differs from v2.0 in two ontologies:
  * DAX v2.3 improves on further direct subtypes of dax:Company
    (new: 18 sectors, old: 11) and adds a further layer (new: 63
    subsectors).
  * IF v1.1 introduces a property if:origin which maps companies
    (either from DAX or EN) to stock exchanges;
    if:StockExchange has subclasses if:XETRA and if:NYSE which
    introduce further subclasses, such as if:DAX, if:TecDAX, or
    if:Euronext;
    this property will be used to record the "origin" of company
    ABox snapshots.

MFO v2.2 makes some refinements in that it comes with full Protege
projects for each of the ontologies, thus you both have N-triple files
and OWL-XML files.
I have furthermore moved to fully expanded namespace names in order to
be compliant with the N-triple specification.
xsd:monetary now has been properly integrated as a new XSD datatype.
As always, each ontology comes with its own 000README.txt file showing
what has changed in the newest version.
Note also that ICB v1.1 has now added German and Spanish labels and
definitions for all classes (v1.0 only English).
Probably the most important benefit is that one can view XEBR using
Protege to pleasantly view the structure of the ontology as we have
modeled it.

MFOv3.0 extends IF (v1.2 to v1.3) and XEBR (v1.1 to v1.2) even further
(only minor updates and corrections), but adds two further ontologies:
  * SKOSv1.0
  * XEBR2XBRLv1.0
XEBR2XBRLv1.0 can be seen as an additional interface ontology which links
concepts from the Belgium and Spanish XBRL ontology (which is NOT given
explicitly) with concepts from the core XEBR ontology.
This is achieved by using informally-described properties from the SKOS
specification. In order to achieve this, we have implemented an OWL Full
SKOS ontology.
