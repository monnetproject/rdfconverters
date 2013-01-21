import argparse
# Superhack! Workaround for https://github.com/lxml/lxml/issues/95.
# If that issue is resolved, set the version as a minimum dependency in setup.py and remove this.
import lxml._elementpath
class FakeDictionary:
    def clear(self):
        pass
    def __getitem__(self, item): 
        raise KeyError()
    def __setitem__(self, blah, blahhh): 
        pass
    def __len__(self):
        return 0
lxml._elementpath._cache = FakeDictionary()

from lxml import etree
import os
from rdfconverters import util
from rdfconverters.xbrl2rdf.xbrl import *
from rdfconverters.xbrl2rdf.converter import RDFConverter

rdf_converter = RDFConverter()

def convert(inputfile, taxonomy=None):
    with open(inputfile) as f:
        tree = etree.parse(f)

    if taxonomy:
        xbrl_instance = XBRLFactory.from_name(tree, taxonomy)
        print("Interpreted %s as '%s':" % (os.path.basename(inputfile), xbrl_instance))
    else:
        xbrl_instance = XBRLFactory.detect_and_instantiate(tree)
        if xbrl_instance is None:
            raise Exception("Could not detect taxonomy in %s" % inputfile)
        print("Detected %s as '%s':" % (os.path.basename(inputfile), xbrl_instance))

    xbrl_instance.parse_report()

    graph = rdf_converter.convert(xbrl_instance)

    return graph

def main():
    def _convert(inputfile):
        return convert(inputfile, taxonomy=args.force_taxonomy)

    parser = argparse.ArgumentParser(
        description='Convert an XBRL instance from a local taxonomy into xEBR RDF format.'
    )
    command_builder = util.CommandBuilder(parser)
    command_builder.add_convert(_convert)
    command_builder.add_batch_convert(_convert, 'xbrl')
    parser.add_argument("--force-taxonomy", choices=["es-pgc", "be"], dest='force_taxonomy',
        help="Force the converter to interpret the input file(s) as the given taxonomy, rather " +
            "than detecting the taxonomy automatically")

    args = parser.parse_args()
    command_builder.execute(args)


if __name__ == '__main__':
    main()
