# XML Format

ie2rdf expects a standard XML format as input. The nodes and attributes are as follows:

1. The root tag should be `<companyprofile>`
2. Children of the root node should contain features ("feature node"), the tag name and attributes of which are described below.
3. Nested inside each feature an <annotation> field which specifies the part of the unstructured text from which the information is extracted.

The name of the input file without the file extension is used as the identifying cp: node in the output.

### Features

- company:
    - name
- activity:
    - id       (GICS code, see included gics-nr-descr.txt)
    - label    (GICS value, optional)
- location:
    - value 
- employees
    - number   (integer)
- customers
    - kind     (see out_dax-en-26.xml for example)
    - number   (integer)
- sales/revenue/profit/income/turnover
    - date     (year only)
    - value    (xsd:monetary, i.e. number without decimals followed by an ISO4217 currency code)

# Generating XML with GATE

The `gatexmlgenerator` directory contains tools to generate the XML format from GATE files. It is somewhat of a Frankenstein solution but it is unlikely to be reused as a whole.

- `gateannotator` is a Java project which takes the path to a GATE .xgapp file, an input folder and an output folder as arguments, and annotates the text files in the input folder using GATE, mirroring the results in the output folder.
- `gateannotator.py` is a Python bridge which runs the GATEAnnotator Java project.
- `ie.py` is Noëmi Aepli's work, which converts annotated data into the above XML format for use with ie2rdf.
- `gatexmlgenerator.py` encapsulates all of the above in a single task.
- The `DAXGATE` folder contains a GATE project which was developed to extract information from DAX profiles.
