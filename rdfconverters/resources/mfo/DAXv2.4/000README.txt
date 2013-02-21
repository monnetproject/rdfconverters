
(C) Hans-Ulrich Krieger, DFKI-LT

The DAX ontology, version 2.1 has been defined along the lines of the
crawled data from the DAX company pages.
Some rearrangements have been made as compared to version 1 in order
to avoid "container" classes, such as dax:Address or dax:Amount.

Thus the range of dax:totalCapitalStock no longer is dax:Amount, but
instead a newly defined XSD datatype, called xsd:monetary.

Since we have deleted dax:Address, the datatype properties dax:country,
dax:city, and dax:street are now directly defined on dax:Company.

Furthermore, I have cross-classified every property as being either a
SYNCHRONIC or DIACHRONIC property.

Interfacing DAX to other sub-ontologies is no longer expressed in the
ontology, but instead in a separate interface ontology, called IF.

In addition, I have made the string-based classification of the 11
DAX sectors into direct subclasses of dax:Company.

It is worth noting that singleton instances exist for the following
classes:
  * dax:AccountingStandard -> dax:accounting_standard_singleton
  * dax:GAAP -> dax:gaap_singleton
  * dax:IFRS -> dax:ifrs_singleton
  * dax:MarketSegment -> dax:market_segment_singleton
  * dax:OpenMarket -> dax:open_market_singleton
  * dax:RegulatedMarket -> dax:regulated_market_singleton
  * dax:TransparencyStandard -> dax:transparency_standard_singleton
  * dax:EntryStandard -> dax:entry_standard_singleton
  * dax:FirstQuotationBoard -> dax:first_quotation_board_singleton
  * dax:GeneralStandard -> dax:general_standard_singleton
  * dax:PrimeStandard -> dax: prime_standard_singleton
These instances should always be used when filling a company template,
since no properties are defined on those classes.

I have used Protege to define the OWL-XML version (extension: owl)
and the Raptor RDF library to generate a corresponding N-triple file
(extension: nt).
To view the OWL version of the ontology, use Protege (recommendation:
a 3.4.X version) and load the pprj file, using "Open".

CHANGES in Version 2.2
----------------------
The property dax:hasReport has been deleted.
Side remark: Instead, hasReport is now part of the IF namespace and
connects
  + dax:Company
  + en:Company
  + nace:IndustrySector
  +icb:ICB
with xebr:Report.

CHANGES in Version 2.3
----------------------
The subtype hierarchy under Company has been expanded by further direct
subtypes, together with a second layer (subsectors) which come with a
description/definition of each subsector for both English and German.

CHANGES in Version 2.4
----------------------
Our own XSD datatype monetary is now properly integrated as an XSD datatype
(and not as a Class), so that Protege can display it for property
dax:totalCapitalStock.
