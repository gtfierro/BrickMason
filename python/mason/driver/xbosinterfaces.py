import re
from rdflib import Namespace, URIRef, Literal
from xbos.services.pundat import DataClient
from xbos.services.brick import Generator as XBOSGenerator
import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BF = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')


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


i_xbos_light_points = {
    'brightness': BRICK.Lighting_System_Luminance_Command,
    'state': BRICK.Lighting_State,
}

i_xbos_plug_points = {
    'state': BRICK.On_Off_Command,
    'power': BRICK.Electric_Meter,
}



class Generator(object):
    def __init__(self, G, cfg):
        self.BLDG = cfg['BLDG']
        self.namespace = cfg['namespace']
        self.client = DataClient(archivers=[cfg['archiver']])
        generator = XBOSGenerator(self.BLDG, self.client)

        logging.info("Querying for Thermostats")
        thermostats = {}
        result = self.client.query('select path where uri like "{0}" and uri like "thermostat" and name = "state";'.format(self.namespace))

        for doc in result['metadata']:
            path = doc['path']

            # extract zone name
            zone_name = re.match(r'.*/([^/]+)/i.xbos.thermostat', path)
            if zone_name is not None:
                zone_name = zone_name.groups()[0]
            else:
                logging.warning("No zone found")
                continue
            logging.info('HVAC Zone: {0}'.format(zone_name))

            urisuffix = re.match(r'[^/]+(/.*/i.xbos.thermostat)', path)
            if urisuffix is not None:
                urisuffix = urisuffix.groups()[0]
            else:
                logging.warning("No URI suffix found for {0}".format(zone_name))
                continue
            logging.info('Tstat URI: {0}'.format(urisuffix))

            rtu_name = zone_name+"_RTU"
            G.add((self.BLDG[rtu_name], RDF.type, BRICK.RTU))
            G.add((self.BLDG[rtu_name], BF.feeds, self.BLDG[zone_name]))
            G.add((self.BLDG[zone_name], RDF.type, BRICK.HVAC_Zone))
            for t in self.add_xbos_thermostat(self.BLDG[zone_name+'_tstat'], self.namespace + urisuffix, self.BLDG[rtu_name]):
                G.add(t)
            thermostats[zone_name] = self.BLDG[zone_name+'_tstat']


        logging.info("Querying for Eagle Meters")
        result = self.client.query('select uuid, path where uri like "{0}" and originaluri like "eagle" and name = "demand";'.format(self.namespace))
        for doc in result['metadata']:
            path = doc['path']
            meter_name = 'building_meter'
            G.add((BRICK.Building_Electric_Meter, RDF.type, OWL.Class))
            G.add((BRICK.Building_Electric_Meter, RDFS.subClassOf, BRICK.Electric_Meter))
            G.add((self.BLDG[meter_name], RDF.type, BRICK.Building_Electric_Meter))
            G.add((self.BLDG[meter_name], BF.uuid, Literal(doc['uuid'])))
            urisuffix = re.match(r'[^/]+(/.*/i.meter)', path)
            if urisuffix is not None:
                urisuffix = urisuffix.groups()[0]
            else:
                logging.warning("No URI suffix found for {0}".format(zone_name))
                continue
            logging.info('Tstat URI: {0}'.format(urisuffix))
            G.add((self.BLDG[meter_name], BF.uri, Literal(self.namespace + urisuffix)))
            for tstat in thermostats.values():
                G.add((tstat, BF.hasPoint, self.BLDG[meter_name]))

        logging.info("Querying for TED")
        result = self.client.query('select uuid, path where uri like "{0}" and originaluri like "MTU1" and name like "demand";'.format(self.namespace))
        for doc in result['metadata']:
            path = doc['path']
            meter_name = 'building_meter'
            G.add((BRICK.Building_Electric_Meter, RDF.type, OWL.Class))
            G.add((BRICK.Building_Electric_Meter, RDFS.subClassOf, BRICK.Electric_Meter))
            G.add((self.BLDG[meter_name], RDF.type, BRICK.Building_Electric_Meter))
            G.add((self.BLDG[meter_name], BF.uuid, Literal(doc['uuid'])))
            urisuffix = re.match(r'[^/]+(/.*/i.xbos.meter)', path)
            if urisuffix is not None:
                urisuffix = urisuffix.groups()[0]
            else:
                logging.warning("No URI suffix found for {0}".format(zone_name))
                continue
            logging.info('Tstat URI: {0}'.format(urisuffix))
            G.add((self.BLDG[meter_name], BF.uri, Literal(self.namespace + urisuffix)))
            for tstat in thermostats.values():
                G.add((tstat, BF.hasPoint, self.BLDG[meter_name]))

    def add_xbos_thermostat(self, node, uri, controls=None):
        rest_of_uri = '/'.join(uri.split("/")[1:])
        self.namespace = uri.split("/")[0]
        md = self.client.query("select name, uuid where namespace = '{0}' and originaluri like '{1}'".format(self.namespace, rest_of_uri)).get('metadata')
        triples = []
        triples.append((node, RDF.type, BRICK.Thermostat))
        triples.append((node, BF.uri, Literal(uri)))

        triples.append((BRICK.Thermostat_Status, RDFS.subClassOf, BRICK.Status))
        triples.append((BRICK.Thermostat_Status, RDF.type, OWL.Class))
        triples.append((BRICK.Thermostat_Mode_Command, RDFS.subClassOf, BRICK.Command))
        triples.append((BRICK.Thermostat_Mode_Command, RDF.type, OWL.Class))

        if controls is not None:
            triples.append((node, BF.controls, controls))
        for doc in md:
            if doc['name'] in i_xbos_thermostat_points.keys():
                pointname = self.BLDG[node.split('#')[-1]+"_"+doc['name']]
                triples.append((pointname, RDF.type, i_xbos_thermostat_points[doc['name']]))
                triples.append((node, BF.hasPoint, pointname))
                triples.append((pointname, BF.uuid, Literal(doc['uuid'])))
        return triples

    def add_xbos_light(self, node, uri, controls=None):
        rest_of_uri = '/'.join(uri.split("/")[1:])
        namespace = uri.split("/")[0]
        md = self.client.query("select name, uuid where namespace = '{0}' and originaluri like '{1}'".format(namespace, rest_of_uri)).get('metadata')
        triples = []
        triples.append((node, RDF.type, BRICK.Lighting_System))
        triples.append((node, BF.uri, Literal(uri)))
        if controls is not None:
            triples.append((node, BF.controls, controls))
        for doc in md:
            if doc['name'] in i_xbos_light_points.keys():
                pointname = self.BLDG[node.split('#')[-1]+"_"+doc['name']]
                triples.append((pointname, RDF.type, i_xbos_light_points[doc['name']]))
                triples.append((node, BF.hasPoint, pointname))
                triples.append((pointname, BF.uuid, Literal(doc['uuid'])))
        return triples

    def add_xbos_plug(self, node, uri):
        rest_of_uri = '/'.join(uri.split("/")[1:])
        namespace = uri.split("/")[0]
        md = self.client.query("select name, uuid where namespace = '{0}' and originaluri like '{1}'".format(namespace, rest_of_uri)).get('metadata')
        triples = []
        triples.append((BRICK.PlugStrip, RDFS.subClassOf, BRICK.Equipment))
        triples.append((BRICK.PlugStrip, RDF.type, OWL.Class))
        triples.append((node, RDF.type, BRICK.PlugStrip))
        triples.append((node, BF.uri, Literal(uri)))
        for doc in md:
            if doc['name'] in i_xbos_plug_points.keys():
                pointname = self.BLDG[node.split('#')[-1]+"_"+doc['name']]
                triples.append((pointname, RDF.type, i_xbos_plug_points[doc['name']]))
                triples.append((node, BF.hasPoint, pointname))
                triples.append((pointname, BF.uuid, Literal(doc['uuid'])))
        return triples
