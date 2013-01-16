from rdfconverters import util
import argparse
import os
from rdflib import Graph

def main():
    types = ['n3', 'xml', 'nt']

    parser = argparse.ArgumentParser(
        description='Utility to merge all RDF graphs in a directory into one file')
    parser.add_argument('-f', '--format', choices=types, default='n3', help="Output format")
    parser.add_argument('input', help='Input folder')
    parser.add_argument('output', help='Output file')
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        raise IOError("Input directory does not exist or is not a directory")

    util.merge_graphs_in_directory(args.input, args.output, format=args.format)

if __name__ == '__main__':
    main()
