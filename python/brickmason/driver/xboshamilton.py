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

hamilton_points = {
    'air_temp': BRICK.Zone_Temperature_Sensor,
    'lux': BRICK.Illumination_Sensor,
    'air_rh': BRICK.Relative_Humidity_Sensor,
    'presence': BRICK.Occupancy_Sensor,
}

class Generator(object):
    def __init__(self, G, cfg):
        self.G = G
        self.BLDG = cfg['BLDG']
        self.namespace = cfg['namespace']
        ns_uuid = uuid.UUID(cfg['namespace_uuid'])
        sensors = cfg['sensors']
        for sensoruri in sensors:
            
            sensor_name = re.match(r'.*/([^/]+)/i.temperature', sensoruri)
            if sensor_name is not None:
                sensor_name = sensor_name.groups()[0]
            else:
                logging.warning("No sensor name found")
                continue
            sensor_name = 'hamilton_{0}'.format(sensor_name[-4:]).lower()

            sensoruri_iface = re.match(r'[^/]+(/.*/i.temperature)', sensoruri)
            if sensoruri_iface is not None:
                sensoruri_iface = sensoruri_iface.groups()[0]
            else:
                logging.warning("No URI suffix found for {0}".format(sensor_name))
                continue
            logging.info('sensor URI: {0}'.format(sensoruri_iface))
            for archiverequestfile in cfg.get('archive_requests', []):
                logging.info("Using Archive Request %s", archiverequestfile)
                archive_request = yaml.load(open(archiverequestfile))
                # generate uuids
                for aspect in archive_request['Archive']:
                    match = re.match(aspect['URIMatch'], sensoruri)
                    newURItemplate = aspect['URIReplace']
                    if match is None: continue
                    for i in range(len(match.groups())):
                        newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                    name = aspect['Name']
                    pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + name))
                    self.G.add((self.BLDG[sensor_name+'_'+aspect['Name']], RDF.type, hamilton_points[aspect['Name']]))
                    self.G.add((self.BLDG[sensor_name+'_'+aspect['Name']], BF.uri, Literal('{0}{1}'.format(self.namespace, sensoruri_iface))))
                    self.G.add((self.BLDG[sensor_name+'_'+aspect['Name']], BF.uuid, Literal(pointuuid)))
                    

