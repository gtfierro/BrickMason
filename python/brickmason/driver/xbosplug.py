import re
from xbos import get_client
from rdflib import Namespace, URIRef, Literal
import yaml
import uuid
import coloredlogs, logging
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')

i_xbos_plug_points = {
    'state': BRICK.On_Off_Command,
    'power': BRICK.Electric_Meter,
}

bw2 = get_client()
def resolve_pattern(pattern, namespace=None):
    prefix = re.match(r'(.*/i.xbos.[a-zA-Z_]+)', pattern)
    if prefix is None: return []
    lastalive = '{0}/!meta/lastalive'.format(prefix.groups()[0])
    logging.info("trying %s", lastalive)
    po = bw2.query(lastalive)
    if namespace is not None:
        def repl(uri):
            uri = uri.split('/')
            return namespace + '/' + '/'.join(uri[1:])
        return [repl(msg.uri) for msg in po if len(msg.payload_objects) > 0]
    else:
        return [msg.uri for msg in po if len(msg.payload_objects) > 0]
    

class Generator(object):
    def __init__(self, G, cfg):
        self.G = G
        self.BLDG = cfg['BLDG']
        self.namespace = cfg['namespace']
        ns_uuid = uuid.UUID(cfg['namespace_uuid'])
        plugs = cfg['plugs']
        for pattern in plugs:
            for pluguri in resolve_pattern(pattern, namespace=self.namespace):
                pluguri_iface = re.match(r'[^/]+(/.*/i.xbos.plug)', pluguri)
                if pluguri_iface is not None:
                    pluguri_iface = pluguri_iface.groups()[0]
                else:
                    logging.warning("No URI suffix found for {0}".format(pluguri))
                    continue
                logging.info('plug URI: {0}'.format(pluguri_iface))

                # extract plug name
                plug_name = re.match(r'.*/([^/]+)/s.[^/]+/[^/]+/i.xbos.plug', pluguri)
                if plug_name is not None:
                    plug_name = plug_name.groups()[0]
                else:
                    logging.warning("No plug found")
                    continue
                uri = Literal('{0}{1}'.format(self.namespace, pluguri_iface))

                # add triples for RTU, zone
                self.G.add((self.BLDG[plug_name], RDF.type, BRICK.PlugStrip))
                self.G.add((self.BLDG[plug_name], BF.uri, uri))

                for archiverequestfile in cfg.get('archive_requests', []):
                    logging.info("Using Archive Request %s", archiverequestfile)
                    archive_request = yaml.load(open(archiverequestfile))
                    # generate uuids
                    for aspect in archive_request['Archive']:
                        match =  re.match(aspect['URIMatch'], pluguri)
                        newURItemplate = aspect['URIReplace']
                        if match is None: continue
                        for i in range(len(match.groups())):
                            newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                        name = aspect['Name']
                        if name not in i_xbos_plug_points:
                            logging.warning("skipping %s for %s", name, pluguri_iface)
                            continue
                        pointname = plug_name+'_'+name
                        pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + aspect['Name']))
                        self.G.add((self.BLDG[pointname], RDF.type, i_xbos_plug_points[name]))
                        self.G.add((self.BLDG[pointname], BF.uuid, Literal(pointuuid)))
                        self.G.add((self.BLDG[pointname], BF.uri, uri))
                        self.G.add((self.BLDG[plug_name], BF.hasPoint, self.BLDG[pointname]))
