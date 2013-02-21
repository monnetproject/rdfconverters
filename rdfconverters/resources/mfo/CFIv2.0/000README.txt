
(C) Hans-Ulrich Krieger, DFKI-LT

The Classification of Financial Instruments version 2 ontology (CFI v2.0)
differs quite drastically from version 1.
Version 1 used a six-level deeply nested subclass ontology which reflected
the CFI codes as stated in ISO 10962.
Version 1 was hand-written and incomplete, missing a lot of the possible
codes.
Version 2 now uses only a single class, called cfi:CFI, on which six
properties are defined that are able to "access" the individual characters
of a code 123456, viz.,
  1 = cfi:category
  2 = cfi:group
  3 = cfi:first (attribute)
  4 = cfi:second (attribute)
  5 = cfi:third (attribute)
  6 = cfi:fourth (attribute)
These properties are functional datatype properties which map onto the
xsd:string datatype.
