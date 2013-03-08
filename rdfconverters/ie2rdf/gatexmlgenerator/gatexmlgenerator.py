import sys
import os
from rdfconverters.ie2rdf.gatexmlgenerator import gateannotator, ie
from rdfconverters import util
import shutil

def main():
  if len(sys.argv) != 5:
    print("Usage: %s xgappfile source_folder gate_output_folder target_folder" % (sys.argv[0]));
    print("Source folder should only contain plaintext profile data for processing");
    return

  _, xgappfile, source_folder, gate_output_folder, target_folder = sys.argv

  xgapp_canonical = os.path.realpath(xgappfile)
  src_canonical = os.path.realpath(source_folder)
  target_canonical = os.path.realpath(target_folder)

  try:
    os.makedirs(gate_output_folder)
  except:
    pass
  gateannotator.run_gate_annotator(xgapp_canonical, src_canonical, gate_output_folder)

  for infile, outfile in util.traverse_mirror(gate_output_folder, target_folder):
    print("*** Converting %s to %s" % (infile, outfile))
    xml = ie.convert_file(infile)
    with open(outfile, "w") as f:
      f.write(xml)

if __name__ == '__main__':
  main()
