import sys
import os
from rdfconverters.ie2rdf.gatexmlgenerator import gateannotator, ie
from rdfconverters import util
import shutil

GATEANNOTATOR_TMP = "/tmp/gateannotator"

def main():
  if len(sys.argv) != 4:
    print("Usage: %s xgappfile source_folder target_folder" % (sys.argv[0]));
    print("Source folder should only contain plaintext profile data for processing");
    return

  _, xgappfile, source_folder, target_folder = sys.argv

  xgapp_canonical = os.path.realpath(xgappfile)
  src_canonical = os.path.realpath(source_folder)
  target_canonical = os.path.realpath(target_folder)

  if os.path.exists(GATEANNOTATOR_TMP):
    shutil.rmtree(GATEANNOTATOR_TMP)
  os.makedirs(GATEANNOTATOR_TMP)
  gateannotator.run_gate_annotator(xgapp_canonical, src_canonical, GATEANNOTATOR_TMP)

  for infile, outfile in util.traverse_mirror(GATEANNOTATOR_TMP, target_folder):
    print("*** Converting %s to %s" % (infile, outfile))
    xml = ie.convert_file(infile)
    with open(outfile, "w") as f:
      f.write(xml)

if __name__ == '__main__':
  main()
