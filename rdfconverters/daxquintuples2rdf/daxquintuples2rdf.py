import re
import io
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import XSD
import sys
import os
import html.parser
import argparse
from rdfconverters import util
from rdfconverters.util import NS


class QuintupleReader:
    '''
    Reads and cleans ABOX files, handling inconsistencies in the supplied data.
    '''

    def __clean(self, s):
        # Decode HTML entities
        s = s.replace('&quot;', '\\"')
        s = html.parser.HTMLParser().unescape(s)

        # Replace dodgy prefixes
        for n in NS:
            s = s.replace('<%s:' % n, '<%s' % NS[n])
        return s

    def read(self, filename):
        # Data is encoded in mac_latin2 (ntriples requires unicode-escape)
        with open(filename, encoding="mac_latin2") as f:
            quintuples = f.read()
        # Encode UTF-8 to unicode-escape
        quintuples = quintuples.encode('unicode-escape').decode('utf8')
        quintuples = quintuples.replace('\\n', '\n').replace('\\"', '\"')
        return self.__clean(quintuples)


class QuintuplesToTriples:
    DATETIME_REGEX = r"\"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\"\^\^<http://www.w3.org/2001/XMLSchema#dateTime>\s*";
    NTUPLEDATES = DATETIME_REGEX * 2 + r"\s*\."

    def __extract_instant(self, quintuples):
        '''
        Snapshot times are specified as a range in files, but start and end are
        the same for all facts. This extracts the dateTime in the file, raising
        an exception if duplicates exist.
        '''
        dates = [date for date in re.findall(self.DATETIME_REGEX, quintuples)]
        if len(set(dates)) > 1:
            raise Exception("Multiple dates in input file")
        return dates[0]

    def to_triples(self, quintuples, format="nt"):
        '''Parse the quintuple data and return an rdflib graph'''

        # Remove the start and end items to convert to triples
        triples = re.sub(self.NTUPLEDATES, ' .', quintuples)

        # Parse triples
        g = Graph()
        for n in NS:
            g.bind(n, NS[n])
        g.parse(data=triples, format=format)

        subject = next(g.subjects(NS['if']['origin'], None))
        instant = self.__extract_instant(quintuples)
        g.add((subject, NS['cp']['instant'],
            Literal(instant, datatype=XSD.dateTime)))

        return g

def convert(inputfile):
    reader = QuintupleReader()
    quintuples = reader.read(inputfile)

    q = QuintuplesToTriples()
    graph = q.to_triples(quintuples)

    return graph


def main():
    parser = argparse.ArgumentParser(description="Converts DFKI Quintuple N-Triple DAX ABOX data to RDF triples")
    command_builder = util.CommandBuilder(parser)
    command_builder.add_convert(convert)
    command_builder.add_batch_convert(convert, 'nt')
    args = parser.parse_args()
    command_builder.execute(args)

if __name__ == '__main__':
    main()

