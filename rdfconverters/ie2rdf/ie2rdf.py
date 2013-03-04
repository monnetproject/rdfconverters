from lxml import etree
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import XSD
from html.parser import HTMLParser
import sys
import os
import re
from rdfconverters import util
from rdfconverters.util import NS
import argparse


class IE2RDF:
    def __init__(self, file_, lang="en"):
        self.lang = lang
        with open(file_, "r") as f:
            self.tree = etree.parse(f)
        self.root = self.tree.getroot()

        self.g = Graph()
        for n in NS:
            self.g.bind(n, NS[n])

        # Note: Filename is used as the identifier of the node, so filename should be
        # the same as the structured instance cp: identifier.
        if len(self.root) > 0:
            self.cp = NS['cp'][os.path.splitext(os.path.basename(file_))[0]]
            self.g.add((self.cp, NS['rdf']['type'], NS['cp']['CompanyProfile']))

    def __make_bnode(self, cpname, cptype, attr):
        b = BNode()
        self.g.add((b, NS['rdf']['type'], NS['cp'][cptype]))

        for k, v in attr.items():
            if not isinstance(v, Literal) or len(str(v)) > 0:
                self.g.add((b, NS['cp'][k], v))

            self.g.add((self.cp, NS['cp'][cpname], b))
        return b

    def __annotate(self, node, annotations):
        self.g.add((node, NS['rdf']['type'], NS['cp']['Unstructured']))
        for annotation in annotations:
            self.g.add((node, NS['cp']['annotation'], Literal(annotation, lang=self.lang)))

    def convert(self):
        def pop(el, attr):
            return HTMLParser().unescape(el.attrib.pop(attr).strip())

        for el in self.root:
            if el.tag == 'company':
                name = pop(el, 'name')
                attr = {'stringValue': Literal(name)}
                node = self.__make_bnode('companyName', 'StringValue', attr)
            elif el.tag == 'activity':
                id_ = pop(el, 'id')
                pop(el, 'label')
                attr = {'sectorValue': NS['icb'][id_]}
                node = self.__make_bnode('sector', 'SectorValue', attr)
            elif el.tag == 'location':
                value = pop(el, 'value')
                attr = {'stringValue': Literal(value)}
                node = self.__make_bnode(el.tag, 'StringValue', attr)
            elif el.tag == 'employees':
                number = pop(el, 'number')
                attr = {'integerValue': Literal(number, datatype=XSD.integer)}
                node = self.__make_bnode(el.tag, 'IntegerValue', attr)
            elif el.tag == 'customers':
                kind = pop(el, 'kind')
                number = pop(el, 'number')
                attr = {}
                if number:
                    attr['number'] = Literal(number, datatype=XSD.integer)
                if kind:
                    attr['text'] = Literal(kind)
                node = self.__make_bnode(el.tag, 'NumberTextValue', attr)
            elif el.tag == 'unknownMonetaryValue':
                # Ignore these
                continue
            elif el.tag in ['revenue', 'sales', 'income', 'profit', 'turnover']:
                date = pop(el, 'date')
                value = pop(el, 'value')
                if not re.match('^\d+[A-Z]{3}', value):
                    print("WARNING: Ignoring node. Invalid monetary value %s" % value)
                    continue
                attr = {'date': Literal(date, datatype=XSD.gYear),
                    'monetaryValue': Literal(value, datatype=XSD.monetary)}
                node = self.__make_bnode(el.tag, 'MonetaryValue', attr)
            else:
                raise Exception("Unexpected element found: %s" % el.tag)

            if len(el.attrib) > 0:
                raise Exception("Unexpected attributes: " + ','.join(el.attrib.keys()))

            self.__annotate(node, [annotation.text.strip() for annotation in el])

        return self.g



def main():
    def convert(inputfile):
        g = IE2RDF(inputfile, args.lang)
        graph = g.convert()
        return graph

    parser = argparse.ArgumentParser(description='Convert XML files from information extraction to the CP ontology RDF format')

    command_builder = util.CommandBuilder(parser)
    convert_command = command_builder.add_convert(convert)
    convert_command.add_argument('lang', help="xml:lang code to be used for annotations")

    batchconvert_command = command_builder.add_batch_convert(convert, 'xml')
    batchconvert_command.add_argument('lang', help="xml:lang code to be used for annotations")

    args = parser.parse_args()
    command_builder.execute(args)

if __name__ == '__main__':
    main()
