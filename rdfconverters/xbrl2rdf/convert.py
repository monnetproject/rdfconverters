import argparse

from xbrl import *
from writer import RDFWriter

def convert(inputfile, language='be', format='n3'):
   # Convert file
   if language == 'es':
       x = XBRLSpanish(inputfile)
   elif language == 'be':
       x = XBRLBelgian(inputfile)
   else:
       print("Unrecognised language code \"%s\"" % language)
       import sys
       sys.exit(0)

   r = RDFWriter(x)
   output = r.generate_rdf(format)
   return output

if __name__ == '__main__':
   # Parse arguments
   parser = argparse.ArgumentParser(description='Convert an XBRL instance in XML format to RDF.')
   parser.add_argument('input', metavar='Input File', type=str,
                      help='Location of the input file')
   parser.add_argument('language', metavar='Language', type=str,
                      help='Language ("es" for Spanish XBRL, "be" for Belgian XBRL')
   parser.add_argument("-f", "--format", dest='format', action='store', default='n3',
                      help='Output format (e.g. n3, turtle, xml). Default is n3')
   args = parser.parse_args()
   convert(args.inputfile, args.language, args.format)
   print(output)
