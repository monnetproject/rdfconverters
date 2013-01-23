import subprocess
import os

def run_gate_annotator(xgappfile, source_folder, target_folder):
    # Using __file__ instead of pkg_resources prevents .egg being packaged which would make Java execution impossible
    cwd = os.path.split(os.path.abspath(__file__))[0] + '/gateannotator'
    mvn = subprocess.Popen(['mvn', 'exec:java', '-Dexec.args=%s %s %s' % (xgappfile, source_folder, target_folder)], cwd=cwd)
    mvn.wait()

