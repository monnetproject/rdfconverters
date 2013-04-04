from rdfconverters.xbrl2rdf import xbrl2rdf
import time
from os.path import abspath, dirname
import cProfile
import sys

t1 = int(round(time.time() * 1000))

inf = dirname(abspath( __file__ )) + "/fixtures"
sys.argv = ['xbrl2rdf', 'batchconvert', inf, inf+'/temp']

cProfile.run('xbrl2rdf.main()', 'xbrl2rdf.profile')

t2 = int(round(time.time() * 1000))

import pstats
p = pstats.Stats('xbrl2rdf.profile')
p.sort_stats(2).print_stats()

print ("Time (ms): %s" % (t2-t1))
