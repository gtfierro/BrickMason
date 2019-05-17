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

i_xbos_light_points = {
    'brightness': BRICK.Lighting_System_Luminance_Command,
    'ambient': BRICK.Ambient_Illumination_Sensor,
    'state': BRICK.Lighting_State,
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
            uri = namespace + '/' + '/'.join(uri[1:])
            return uri
        return [repl(msg.uri) for msg in po if len(msg.payload_objects) > 0]
    else:
        return [msg.uri for msg in po if len(msg.payload_objects) > 0]
    

class Generator(object):
    def __init__(self, G, cfg):
        self.G = G
        self.BLDG = cfg['BLDG']
        self.namespace = cfg['namespace']
        ns_uuid = uuid.UUID(cfg['namespace_uuid'])
        lights = cfg['lights']
        for pattern in lights:
            for lighturi in resolve_pattern(pattern, namespace=cfg['namespace']):
                # extract light name
                light_name = re.match(r'.*/([^/]+)/i.xbos.light', lighturi)
                if light_name is not None:
                    light_name = light_name.groups()[0]
                else:
                    logging.warning("No light name found")
                    continue

                lighturi_iface = re.match(r'[^/]+(/.*/i.xbos.light)', lighturi)
                if lighturi_iface is not None:
                    lighturi_iface = lighturi_iface.groups()[0]
                else:
                    logging.warning("No URI suffix found for {0}".format(light_name))
                    continue
                logging.info('Light URI: {0}'.format(lighturi_iface))
                uri = Literal('{0}{1}'.format(self.namespace, lighturi_iface))
                self.G.add((self.BLDG[light_name], RDF.type, BRICK.Lighting_System))
                self.G.add((self.BLDG[light_name], BF.uri, uri))

                for archiverequestfile in cfg.get('archive_requests', []):
                    logging.info("Using Archive Request %s", archiverequestfile)
                    archive_request = yaml.load(open(archiverequestfile))
                    # generate uuids
                    for aspect in archive_request['Archive']:
                        match =  re.match(aspect['URIMatch'], lighturi)
                        newURItemplate = aspect['URIReplace']
                        if match is None: 
                            continue
                        for i in range(len(match.groups())):
                            newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                        name = aspect['Name']
                        pointname = light_name+'_'+name
                        pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + name))
                        self.G.add((self.BLDG[pointname], RDF.type, i_xbos_light_points[name]))
                        self.G.add((self.BLDG[pointname], BF.uuid, Literal(pointuuid)))
                        self.G.add((self.BLDG[pointname], BF.uri, uri))
                        self.G.add((self.BLDG[light_name], BF.hasPoint, self.BLDG[pointname]))

        if 'occupancy' in cfg:
            occ_sensors = cfg['occupancy']
            for pattern in occ_sensors:
                for occsensoruri in resolve_pattern(pattern, namespace=cfg['namespace']):
                    # extract light name
                    light_name = re.match(r'.*/([^/]+)/i.xbos.occupancy_sensor', occsensoruri)
                    if light_name is not None:
                        light_name = light_name.groups()[0]
                    else:
                        logging.warning("No light name found")
                        continue

                    occsensoruri_iface = re.match(r'[^/]+(/.*/i.xbos.occupancy_sensor)', occsensoruri)
                    if occsensoruri_iface is not None:
                        occsensoruri_iface = occsensoruri_iface.groups()[0]
                    else:
                        logging.warning("No URI suffix found for {0}".format(light_name))
                        continue
                    logging.info('Occupancy Sensor URI: {0}'.format(occsensoruri_iface))
                    uri = Literal('{0}{1}'.format(self.namespace, occsensoruri_iface))
                    self.G.add((self.BLDG[light_name+'_occupancy'], RDF.type, BRICK.Occupancy_Sensor))
                    self.G.add((self.BLDG[light_name+'_occupancy'], BF.uri, uri))
                    self.G.add((self.BLDG[light_name], BF.hasPoint, self.BLDG[light_name+'_occupancy']))

                    for archiverequestfile in cfg.get('archive_requests', []):
                        logging.info("Using Archive Request %s", archiverequestfile)
                        archive_request = yaml.load(open(archiverequestfile))
                        # generate uuids
                        for aspect in archive_request['Archive']:
                            name = aspect['Name']
                            if name != 'occupancy': continue
                            match =  re.match(aspect['URIMatch'], occsensoruri)
                            newURItemplate = aspect['URIReplace']
                            if match is None: continue
                            for i in range(len(match.groups())):
                                newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                            pointname = light_name+'_occupancy'
                            pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + name))
                            print '>',pointuuid
                            self.G.add((self.BLDG[pointname], BF.uuid, Literal(pointuuid)))
                            self.G.add((self.BLDG[pointname], BF.uri, uri))

        if 'meter' in cfg:
            light_meters = cfg['meter']
            for pattern in light_meters:
                for meteruri in resolve_pattern(pattern, namespace=cfg['namespace']):
                    # extract light name
                    light_name = re.match(r'.*/([^/]+)/i.xbos.meter', meteruri)
                    if light_name is not None:
                        light_name = light_name.groups()[0]
                    else:
                        logging.warning("No light name found")
                        continue

                    meteruri_iface = re.match(r'[^/]+(/.*/i.xbos.meter)', meteruri)
                    if meteruri_iface is not None:
                        meteruri_iface = meteruri_iface.groups()[0]
                    else:
                        logging.warning("No URI suffix found for {0}".format(light_name))
                        continue
                    logging.info('Light Meter URI: {0}'.format(meteruri_iface))
                    uri = Literal('{0}{1}'.format(self.namespace, meteruri_iface))
                    self.G.add((self.BLDG[light_name+'_meter'], RDF.type, BRICK.Electric_Meter))
                    self.G.add((self.BLDG[light_name+'_meter'], BF.uri, uri))
                    self.G.add((self.BLDG[light_name], BF.hasPoint, self.BLDG[light_name+'_meter']))

                    for archiverequestfile in cfg.get('archive_requests', []):
                        logging.info("Using Archive Request %s", archiverequestfile)
                        archive_request = yaml.load(open(archiverequestfile))
                        # generate uuids
                        for aspect in archive_request['Archive']:
                            name = aspect['Name']
                            if name != 'power': continue
                            match =  re.match(aspect['URIMatch'], meteruri)
                            newURItemplate = aspect['URIReplace']
                            if match is None: continue
                            for i in range(len(match.groups())):
                                newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                            pointname = light_name+'_meter'
                            pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + name))
                            self.G.add((self.BLDG[pointname], BF.uuid, Literal(pointuuid)))
                            self.G.add((self.BLDG[pointname], BF.uri, uri))
