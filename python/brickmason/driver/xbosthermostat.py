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

# Thermostat config
# namespace UUID: b26d2e62-333e-11e6-b557-0cc47a0f7eea
# archive request yaml file
# thermostats:
# - full URI (ending in i.xbos.thermostat)

i_xbos_thermostat_points = {
    'temperature': BRICK.Temperature_Sensor,
    'relative_humidity': BRICK.Relative_Humidity_Sensor,
    'heating_setpoint': BRICK.Supply_Air_Temperature_Heating_Setpoint,
    'cooling_setpoint': BRICK.Supply_Air_Temperature_Cooling_Setpoint,
    'override': BRICK.Override_Command,
    'fan': BRICK.Fan_Command,
    'state': BRICK.Thermostat_Status,
    'mode': BRICK.Thermostat_Mode_Command,
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
        thermostats = cfg['thermostats']
        for pattern in thermostats:
            for tstaturi in resolve_pattern(pattern, namespace=self.namespace):
                tstaturi_iface = re.match(r'[^/]+(/.*/i.xbos.thermostat)', tstaturi)
                if tstaturi_iface is not None:
                    tstaturi_iface = tstaturi_iface.groups()[0]
                else:
                    logging.warning("No URI suffix found for {0}".format(tstaturi))
                    continue
                logging.info('Tstat URI: {0}'.format(tstaturi_iface))

                # extract zone name
                zone_name = re.match(r'.*/([^/]+)/i.xbos.thermostat', tstaturi)
                if zone_name is not None:
                    zone_name = zone_name.groups()[0]
                else:
                    logging.warning("No zone found")
                    continue
                # fix zone name from mapping if exists
                tstat_mapping = cfg.get('tstat_mapping')
                if tstat_mapping is not None:
                    zone_name =  'HVAC_Zone_'+tstat_mapping.get(zone_name, zone_name)
                else:
                    zone_name = 'HVAC_Zone_'+zone_name
                logging.info('HVAC Zone: {0}'.format(zone_name))


                rtu_name = "RTU_"+zone_name
                tstat_name = zone_name+'_tstat'
                uri = Literal('{0}{1}'.format(self.namespace, tstaturi_iface))

                # add triples for RTU, zone
                self.G.add((self.BLDG[rtu_name], RDF.type, BRICK.RTU))
                self.G.add((self.BLDG[rtu_name], BF.feeds, self.BLDG[zone_name]))
                self.G.add((self.BLDG[zone_name], RDF.type, BRICK.HVAC_Zone))
                self.G.add((self.BLDG[tstat_name], RDF.type, BRICK.Thermostat))
                self.G.add((self.BLDG[tstat_name], BF.controls, self.BLDG[rtu_name]))
                self.G.add((self.BLDG[tstat_name], BF.uri, uri))

                for archiverequestfile in cfg.get('archive_requests', []):
                    logging.info("Using Archive Request %s", archiverequestfile)
                    archive_request = yaml.load(open(archiverequestfile))
                    # generate uuids
                    for aspect in archive_request['Archive']:
                        match =  re.match(aspect['URIMatch'], tstaturi)
                        newURItemplate = aspect['URIReplace']
                        if match is None: continue
                        for i in range(len(match.groups())):
                            newURItemplate = newURItemplate.replace('${0}'.format(i+1), match.groups()[i])
                        name = aspect['Name']
                        pointname = tstat_name+'_'+name
                        pointuuid = uuid.uuid3(ns_uuid, str(newURItemplate + aspect['Name']))
                        self.G.add((self.BLDG[pointname], RDF.type, i_xbos_thermostat_points[name]))
                        self.G.add((self.BLDG[pointname], BF.uuid, Literal(pointuuid)))
                        self.G.add((self.BLDG[pointname], BF.uri, uri))
                        self.G.add((self.BLDG[tstat_name], BF.hasPoint, self.BLDG[pointname]))
