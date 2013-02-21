
(C) Hans-Ulrich Krieger, DFKI-LT

The Euronext ontology version 1 (ENv1.0) is an ontology that centers
around companies as represented on the Euronext web site.

This version is able to represent data about
  * company information
  * ICB
  * CFI
  * several financial numbers for three succeeding years
  * shareholders and their amount in percentages
  * persons involved in the management of the company

CHANGES in Version 1.1
----------------------
Our own XSD datatype monetary is now properly integrated as an XSD datatype
(and not as a Class), so that Protege can display it for property
dax:totalCapitalStock.
