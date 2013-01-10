from convert import convert
import sys
import os

def traverse_mirror(inputdir, outputdir, extension='', outextension=''):
   for root, dirs, files in os.walk(inputdir):
      for file in [f for f in files if (f.upper().endswith('.'+extension.upper().lstrip('.')) or len(extension)==0)]:
         inp=root+'/'+file
         out=outputdir+root[len(inputdir):]
         if not os.path.exists(out):
             os.makedirs(out)
         outf=out+'/'+file

         if outextension:
            outf = os.path.splitext(outf)[0] + '.' + outextension.lstrip('.')

         yield (inp, outf)

if len(sys.argv) >= 4:
   lang = sys.argv[3]
else:
   lang = "be"

for inp, out in traverse_mirror(sys.argv[1], sys.argv[2], 'xbrl', 'ttl'):
   with open(out, "w") as f:
       print (inp, "--->", out)
       f.write(convert(inp, lang))
