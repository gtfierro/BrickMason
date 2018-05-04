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
        meters = cfg['meters']
        for pattern in meters:
            for meteruri in resolve_pattern(pattern, namespace=cfg['namespace']):
                meter_name = re.match(r'.*/([^/]+)/i.xbos.meter', meteruri)
                if meter_name is not None:
                    meter_name = meter_name.groups()[0]
                else:
                    logging.warning("No meter name found")
                    continue

                meteruri_iface = re.match(r'[^/]+(/.*/i.xbos.meter)', meteruri)
                if meteruri_iface is not None:
                    meteruri_iface = meteruri_iface.groups()[0]
                else:
                    logging.warning("No URI suffix found for {0}".format(meter_name))
                    continue
                logging.info('meter URI: {0}'.format(meteruri_iface))
                uri = Literal("{0}{1}".format(self.namespace, meteruri_iface))
                self.G.add((self.BLDG[meter_name], RDF.type, BRICK.Building_Electric_Meter))
                self.G.add((self.BLDG[meter_name], BF.uri, uri))

                for archiverequestfile in cfg.get('archive_requests', []):
                    logging.info("Using Archive Request %s", archiverequestfile)
                    archive_request = yaml.load(open(archiverequestfile))
                    # generate uuids
                    for aspect in archive_request['Archive']:
                        if aspect['Name'] != 'demand': continue
                        match =  re.match(aspect['URIMatch'], meteruri)
                        newURItemplate = aspect['URIReplace']
                        if match is None: continue
                        for i in range(len(match.groups())):
                            newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                        name = aspect['Name']
                        pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + name))
                        self.G.add((self.BLDG[meter_name], BF.uuid, Literal(pointuuid)))
                        self.G.add((self.BLDG[meter_name], BF.uri, uri))

        for meteruri in meters:
            # i.meter
            meter_name = re.match(r'.*/([^/]+)/i.meter', meteruri)
            if meter_name is not None:
                meter_name = meter_name.groups()[0]
            else:
                logging.warning("No meter name found")
                continue

            meteruri_iface = re.match(r'[^/]+(/.*/i.meter)', meteruri)
            if meteruri_iface is not None:
                meteruri_iface = meteruri_iface.groups()[0]
            else:
                logging.warning("No URI suffix found for {0}".format(meter_name))
                continue
            logging.info('meter URI: {0}'.format(meteruri_iface))
            uri = Literal("{0}{1}".format(self.namespace, meteruri_iface))

            self.G.add((self.BLDG[meter_name], RDF.type, BRICK.Building_Electric_Meter))
            self.G.add((self.BLDG[meter_name], BF.uri, uri))

            for archiverequestfile in cfg.get('archive_requests', []):
                logging.info("Using Archive Request %s", archiverequestfile)
                archive_request = yaml.load(open(archiverequestfile))
                # generate uuids
                for aspect in archive_request['Archive']:
                    if aspect['Name'] != 'demand': continue
                    match =  re.match(aspect['URIMatch'], meteruri)
                    newURItemplate = aspect['URIReplace']
                    if match is None: continue
                    for i in range(len(match.groups())):
                        newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                    name = aspect['Name']
                    pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + name))
                    self.G.add((self.BLDG[meter_name], BF.uuid, Literal(pointuuid)))
                    self.G.add((self.BLDG[meter_name], BF.uri, uri))
