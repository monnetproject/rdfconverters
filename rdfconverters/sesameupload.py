service_url="http://localhost:8081/openrdf-sesame/repositories/monnet/rdf-graphs/service?graph="
delete=True
upload=True
upload_mfo=True

import requests
from rdfconverters.util import NS
from pkg_resources import resource_stream

graph_files={
  str(NS['xebr_data']): open('/home/barry/data/merged/xebr_cnmv.n3'),
  str(NS['xebr_data']): open('/home/barry/data/merged/xebr_be.n3'),
  str(NS['cp_data']): open('/home/barry/data/merged/en.n3'),
  str(NS['cp_data']): open('/home/barry/data/merged/enprofiles.n3'),
  str(NS['cp_data']): open('/home/barry/data/merged/daxnew.n3'),
  str(NS['cp_data']): open('/home/barry/data/merged/daxprofiles.n3')
}
if upload_mfo:
    graph_files.update({
        str(NS['cfi']): resource_stream('rdfconverters.resources', 'mfo/CFIv2.0/cfi.n3'),
        str(NS['cp']): resource_stream('rdfconverters.resources', 'mfo/CPv1.0/cp.n3'),
        str(NS['dax']): resource_stream('rdfconverters.resources', 'mfo/DAXv2.4/dax.n3'),
        str(NS['dc']): resource_stream('rdfconverters.resources', 'mfo/DCv1.0/dc.n3'),
        str(NS['en']): resource_stream('rdfconverters.resources', 'mfo/ENv1.1/en.n3'),
        str(NS['icb']): resource_stream('rdfconverters.resources', 'mfo/ICBv1.1/icb.n3'),
        str(NS['if']): resource_stream('rdfconverters.resources', 'mfo/IFv1.3/if.n3'),
        str(NS['nace']): resource_stream('rdfconverters.resources', 'mfo/NACEv2.0/nace.n3'),
        str(NS['skos']): resource_stream('rdfconverters.resources', 'mfo/SKOSv1.0/skos.n3'),
        str(NS['time']): resource_stream('rdfconverters.resources', 'mfo/TIMEv1.1/time.n3'),
        str(NS['xebr2xbrl']): resource_stream('rdfconverters.resources', 'mfo/XEBR2XBRLv1.0/xebr2xbrl.n3'),
        str(NS['xebr']): resource_stream('rdfconverters.resources', 'mfo/XEBRv7.0/xebr.n3'),
    })

if delete:
    for graph in graph_files.keys():
        print("Remotely deleting %s" % graph)
        r = requests.delete(service_url+graph)
        if r.status_code != 204: print("ERROR: ", r.content)

if upload:
    for graph, f in graph_files.items():
        url = service_url+graph
        print("Uploading %s to %s" % (f.name, graph))
        r = requests.post(url, f.read(), headers={'Content-Type': 'application/x-turtle;charset=UTF-8'})
        if r.status_code != 204: print("ERROR: ", r.content)
