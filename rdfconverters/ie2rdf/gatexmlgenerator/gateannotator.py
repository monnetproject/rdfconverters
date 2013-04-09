import subprocess
import os
import sys

def run_gate_annotator(xgappfile, source_folder, target_folder):
    # Using __file__ instead of pkg_resources prevents .egg being packaged which would make Java execution impossible
    cwd = os.path.split(os.path.abspath(__file__))[0] + '/gateannotator'
    mvn = subprocess.Popen(['mvn', 'compile'])
    mvn = subprocess.Popen(['mvn', 'exec:java', '-Dexec.args=%s %s %s' % (xgappfile, source_folder, target_folder)], cwd=cwd)
    mvn.wait()

def main():
    if len(sys.argv) != 3:
        print("Arguments: inputfolder outputfolder")
    xgappfile = "/home/barry/code/rdfconverters/rdfconverters/ie2rdf/gatexmlgenerator/DAXGATE/Application/Daxie.xgapp"
    run_gate_annotator(xgappfile, sys.argv[1], sys.argv[2])

if __name__=='__main__':
    main()

