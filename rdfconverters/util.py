import os
import argparse
import traceback
from rdflib import Namespace, Graph

# To avoid duplication of namespaces across converters
NS = {
   'en': Namespace("http://www.dfki.de/lt/en.owl#"),
   'dax': Namespace("http://www.dfki.de/lt/dax.owl#"),
   'cfi': Namespace("http://www.dfki.de/lt/cfi.owl#"),
   'if': Namespace("http://www.dfki.de/lt/if.owl#"),
   'rdf': Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
   'rdfs': Namespace("http://www.w3.org/2000/01/rdf-schema#"),
   'xsd': Namespace("http://www.w3.org/2001/XMLSchema#"),
   'cp': Namespace("http://www.dfki.de/lt/companyprofile.owl#"),
   'icb': Namespace("http://www.dfki.de/lt/icb.owl#"),
   'dc': Namespace("http://www.dfki.de/lt/dc.owl#"),
   'xebr': Namespace('http://www.dfki.de/lt/xebr.owl#'),
   'xbrl_be': Namespace('http://www.dfki.de/lt/xbrl_be.owl#'),
   'xbrl_es': Namespace('http://www.dfki.de/lt/xbrl_es.owl#'),
   'skos': Namespace('http://www.dfki.de/lt/skos.owl#'),
   'owl': Namespace('http://www.w3.org/2002/07/owl#')
}

def write_graph(graph, outputfile=None, format='n3'):
    '''
    Write graph to stdout, or to a file if outputfile is specified.
    '''
    rdf = graph.serialize(format=format)
    if not outputfile:
        print(rdf.decode('utf-8'))
    else:
        with open(outputfile, "wb") as f:
            f.write(rdf)

def merge_graphs_in_directory(directory, outputfile, format='n3'):
    with open(outputfile, "wb") as f:
        graph=Graph()
        for root, file_ in traverse(directory):
            extension = os.path.splitext(file_)[1].lstrip('.')
            if extension in ['n3', 'xml', 'nt']:
                inputfile = root + file_
                graph.parse(inputfile, format=extension)

        rdf = graph.serialize(format=format)

        f.write(rdf)

def traverse(inputdir, extension=''):
   """
   Generator to recursively traverse a directory, yields a 2-tuple of the directory and filename
   inputdir: root directory to traverse
   extension: only yield files with the given file extension
   """
   for root, dirs, files in os.walk(inputdir):
      if extension:
         files = filter(lambda f: f.lower().endswith('.'+extension.lower().lstrip('.')), files)
      for file in files:
        yield (root + os.sep, file)

def traverse_mirror(inputdir, outputdir, extension='', outextension=''):
   '''
   Generator to recursively traverse directory 'inputdir', yields a 2-tuple with each input file
   and its "mirror image" in 'outputdir'. If outextension is replaced, the extension of the output
   file is changed to outextension. It also creates folders in outputdir if they do not already exist.

   This function is useful for batch conversion of files.
   '''
   for inputroot, inputfile in traverse(inputdir, extension):
      inpf = inputroot + inputfile
      outdir = outputdir + os.sep + inputroot[len(inputdir):]
      if not os.path.exists(outdir):
          os.makedirs(outdir)
      outf = outdir + inputfile

      if outextension:
          outf = os.path.splitext(outf)[0] + '.' + outextension.lstrip('.')

      yield (inpf, outf)

class CommandBuilder:
    '''
    Builds command style arguments (like with git e.g. "git add").
    Exists because many converters share common commands e.g. for batch conversion
    '''

    def __init__(self, parser):
        self.parser = parser
        self.subparsers = parser.add_subparsers(help='commands', dest='command')
        self.commands = {}
        self.added_format_arg = False

    def execute(self, args):
        if args.command in self.commands:
            self.commands[args.command](args)

    def __add_format_arg(self):
        if not self.added_format_arg:
            self.parser.add_argument('-f', '--format', choices=['turtle', 'n3', 'xml', 'nt'],
                default='n3', help="Output format")
            self.added_format_arg = True

    def add_convert(self, convert_function, default_format='n3'):
        self.__add_format_arg()

        parser_convert = self.subparsers.add_parser('convert', help='Convert a single file')
        parser_convert.add_argument('input', help='Input file')
        parser_convert.add_argument('output', nargs='?',
            help="Output file. If not specified, output will go to stdout"
        )

        def command(args):
            graph = convert_function(args.input)
            write_graph(graph, args.output, args.format or default_format)

        self.commands['convert'] = command
        return parser_convert

    def add_batch_convert(self, convert_function, extension, default_format='n3'):
        self.__add_format_arg()

        parser_batchconvert = self.subparsers.add_parser('batchconvert',
            help='Convert a directory of files recursively, mirroring the structure in the output directory')
        parser_batchconvert.add_argument('input', help='Input directory')
        parser_batchconvert.add_argument('output', help='Output directory')

        parser_batchconvert.add_argument('--merge', dest='merge', help="Merge to file")

        def command(args):
            if not os.path.isdir(args.input):
                raise IOError("Input directory does not exist or is not a directory: %s" % args.input)
            if not os.path.exists(args.output):
                os.makedirs(args.output)

            succeeded, failed = 0, 0
            failures = {}
            for inputfile, outputfile in traverse_mirror(args.input, args.output, extension, args.format):
                print(inputfile + " -> " + outputfile)
                try:
                    graph = convert_function(inputfile)
                    write_graph(graph, outputfile, args.format or default_format)
                    succeeded += 1
                except KeyboardInterrupt:
                    return
                except Exception as e:
                    traceback.print_exc()
                    failures[inputfile] = str(e)
                    failed += 1

            print ("%d Attempted; %d Successes; %d Failures" % (succeeded+failed, succeeded, failed))
            if failed > 0:
                print("---------\nFailures:\n---------")
                for filename in sorted(failures):
                    print("%s: %s" % (filename, failures[filename]))


            if args.merge:
                print("Merging graphs to %s" % (args.merge))
                merge_graphs_in_directory(args.output, args.merge, format=args.format)

        self.commands['batchconvert'] = command
        return parser_batchconvert
