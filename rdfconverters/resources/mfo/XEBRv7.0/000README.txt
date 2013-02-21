
(C) Hans-Ulrich Krieger, DFKI-LT

The XEBR ontology has been constructed from the "xEBR Taxonomy-National
Annual Accounts Mapping V3 0" spreadsheet through Java code, specially
written for this extraction.

There is NO OWL-XML file that you can view using, e.g., Protege.
Instead, the Java code directly produces four N-triple files for the
different sections of an XEBR report, viz.,
  * Key Balance Sheet Figures
  * Company Identification
  * Company Officials
  * Company History
I have appended the four files in a single file xebr.nt.

CHANGES in Version 1.1
----------------------
Version 1.1 corrects an error that happened during the automatic
translation of the XEBR ontology.
v1.1 now generates long namespace prefixes which is required by the
N-triple specification.
I have also managed to generate an OWL-XML version of the N-triple
file so that the ontology can be displayed using, e.g., Protege.
Our own non-standard XSD datatype "monetary" has also been integrated
into the v1.1 version of XEBR.

CHANGES in Version 1.2
----------------------
Version 1.2 adds further rdf:type statements for the synthetical superclasses
and their subclasses, stating that they are of type owl:Class -- even though
not really necessary, it seems that Protege needs such descriptions in order
to properly display the XEBR ontology.
Furthermore, a few missing partOf TBox statements have also been added.

CHANGES in Version 2.0 (December 2012)
----------------------
The XEBR-OWL version 2.0 addresses the latest version 7.0 of XEBR, again
given as a MS Excel file.
Version 2.0 addresses further concepts found in XEBRv7 and add another
annotation properties to indicate the version number (1-7) when the concept
was introduced in XEBR.
Version 2.0 also comes with a set of slides I have produced for MFO and TMO
which shows how we have reached the XEBR OWL ontology, given the XEBR
taxonomy.
