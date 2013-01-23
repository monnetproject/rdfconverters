# About

_rdfconverters_ is a suite of command line scripts for converting company profile and XBRL data used in 
the Monnet project to RDF format. The scripts are written in Python 3.

# Installation

Download the package via the Downloads tab on github (or using `git clone`) and `cd` to the root 
directory (which contains setup.py). Then run:

    sudo python3 setup.py install

The command line tools should then be available.

# Tools

* `ie2rdf` - Convert XML files from information extraction to the CompanyProfile ontology RDF format. See the README.md in the ie2rdf directory for more details
* `merge_graphs` - Utility to merge all RDF graphs in a directory into one file
* `daxquintuples2rdf` - Converts Deutsche Borse quintuple data from DFKI into triples.
* `xbrl2rdf` - Convert local XBRL formats into RDF (using the MFO ontologies).
* `en2rdf` - Pulls data from EuroNext stock exchange and converts to RDF.

# Usage

Use the `-h` option to get a list of commands, e.g:

    ie2rdf -h

All tools except `merge_graphs` are command-based, and the `-h` option will print a list of commands. You can also get help about a specific command, e.g: 

    ie2rdf batchconvert -h
