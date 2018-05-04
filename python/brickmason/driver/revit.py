from rdflib import Graph, Namespace, URIRef, Literal
import re
import sys
import pandas as pd
from IPython import embed
from xbos.services.brick import Generator

import coloredlogs, logging
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

def clean(s):
    s = str(s)
    s = s.replace(' ','_')
    return s

class Generator(object):
    def __init__(self, G, cfg):
        #BLDG = Namespace(cfg[
        self.G = G
        filename = cfg['revit_schedule']
        BLDG = cfg['BLDG']
        df = pd.read_csv(filename, delimiter='\t', dtype=object)

        logging.info("Adding rooms and floors")
        for tup in df[df['Room: Number'].notnull()].iterrows():
            room = tup[1]
            name = 'Room_'+clean(room['Room: Number'])
            floor = clean(room['Level'])
            zone = str(room['Space: Zone']).replace(' ','_')

            # add floor and room
            self.G.add((BLDG[name], RDF.type, BRICK.Room))
            self.G.add((BLDG[name], RDF.label, Literal(room['Room: Name'])))

            if floor != 'nan':
                self.G.add((BLDG[floor], RDF.type, BRICK.Floor))
                self.G.add((BLDG[floor], RDF.label, Literal(room['Level'])))
                self.G.add((BLDG[floor], BF.hasPart, BLDG[name]))

            # link room to HVAC zone
            if not zone or zone in ['nan','Default']:
                logging.error('No zone information found')
                continue
            zonename = 'HVAC_Zone_'+zone
            self.G.add((BLDG[name], BF.isPartOf, BLDG[zonename]))
            self.G.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))

        logging.info("Adding HVAC Zones")
        zones = df['Space: Zone'].unique()
        for zone in zones:
            logging.debug('zone> {0}'.format(zone))

        logging.info("Adding lights")
        fixtures = df[df['Category'] == 'Lighting Fixtures']
        for fixture in fixtures.iterrows():
            if fixture[1]['Mark'] and 'Sensor' in str(fixture[1]['Mark']):
                name = clean(fixture[1]['Mark'])
                room = 'Room_'+clean(fixture[1]['Room: Number'])
                zone = str(fixture[1]['Space: Zone']).replace(' ','_')

                if name != 'nan':
                    # add lighting and link to room
                    logging.info("Adding light {0}".format(name))
                    self.G.add((BLDG[name], RDF.type, BRICK.Lighting_System))
                    self.G.add((BLDG[name], RDF.label, Literal(fixture[1]['Mark'])))
                    self.G.add((BLDG[name], BF.feeds, BLDG[room]))
                    self.G.add((BLDG[name], BF.hasLocation, BLDG[room]))
                if not zone or zone in ['nan','Default']:
                    logging.error('No zone information found')
                    continue
                zonename = 'HVAC_Zone_'+zone
                self.G.add((BLDG[room], BF.isPartOf, BLDG[zonename]))

        # add dampers
        logging.info('Adding dampers')
        for item in df[df['Category'] == 'Air Terminals'].iterrows():
            item = item[1]
            room = 'Room_'+clean(item['Room: Number'])
            if item['Family'] == 'Return Diffuser':
                dmp_id = 'return_damper_' + str(item['Mark'])
                self.G.add((BLDG[dmp_id], RDF.type, BRICK.Return_Air_Damper))
                self.G.add((BLDG[dmp_id], BF.isFedBy, BLDG[room]))
            if item['Family'] == 'Supply Diffuser':
                dmp_id = 'supply_damper_' + str(item['Mark'])
                self.G.add((BLDG[dmp_id], RDF.type, BRICK.Supply_Air_Damper))
                self.G.add((BLDG[dmp_id], BF.feeds, BLDG[room]))

        logging.info("Adding RTUs and Zones")
        for item in df[(df['Category'].astype('str') == 'Mechanical Equipment') & (df['Type Mark'].astype('str') == 'RTU')].iterrows():
            item = item[1]
            zone = str(item['Mark']).replace(' ','_')

            # add RTU
            rtuname = 'RTU_'+zone
            self.G.add((BLDG[rtuname], RDF.type, BRICK.Rooftop_Unit))

            if not zone or zone in ['nan','Default']:
                logging.error('No zone information found')
                continue
            zonename = 'HVAC_Zone_'+zone
            self.G.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))
            self.G.add((BLDG[rtuname], BF.feeds, BLDG[zonename]))

        logging.info('Adding thermostat')
        for item in df[(df['Family'] == 'Thermostat_573')].iterrows():
            item = item[1]
            zone = str(item['Space: Zone']).replace(' ','_')
            if not zone or zone in ['nan','Default']:
                logging.error('No zone information found')
                continue
            zonename = 'HVAC_Zone_'+zone
            tstatname = zonename + '_tstat'
            rtuname = 'RTU_'+zonename
            roomname = 'Room_'+clean(item['Room: Number'])
            self.G.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))
            self.G.add((BLDG[tstatname], RDF.type, BRICK.Thermostat))
            self.G.add((BLDG[tstatname], BF.controls, BLDG[rtuname]))
            self.G.add((BLDG[tstatname], BF.hasLocation, BLDG[roomname]))

        logging.info('Adding Hamilton sensor')
        sensors = []
        for item in df[(df['Family'] == 'Hamilton_Simple')].iterrows():
            item = item[1]
            hamilton_id = str(item['Comments'])[1:] # remove leading x
            room = 'Room_'+clean(item['Room: Number'])
            logging.warning("Hamilton> {0}".format(hamilton_id))
            name = "hamilton_{0}".format(hamilton_id).lower()
            #print basename, name
            sensors.append((BLDG[name+'_air_temp'], RDF.type, BRICK.Zone_Temperature_Sensor))
            sensors.append((BLDG[name+'_air_temp'], BF.hasLocation, BLDG[room]))
            sensors.append((BLDG[name+'_air_temp'], BF.isPointOf, BLDG[room]))

            #name = find(G, BRICK.Occupancy_Sensor, basename)
            sensors.append((BLDG[name+'_presence'], RDF.type, BRICK.Occupancy_Sensor))
            sensors.append((BLDG[name+'_presence'], BF.hasLocation, BLDG[room]))
            sensors.append((BLDG[name+'_presence'], BF.isPointOf, BLDG[room]))

            #name = find(G, BRICK.Relative_Humidity_Sensor, basename)
            sensors.append((BLDG[name+'_air_rh'], RDF.type, BRICK.Relative_Humidity_Sensor))
            sensors.append((BLDG[name+'_air_rh'], BF.hasLocation, BLDG[room]))
            sensors.append((BLDG[name+'_air_rh'], BF.isPointOf, BLDG[room]))

            #name = find(G, BRICK.Illumination_Sensor, basename)
            sensors.append((BLDG[name+'_lux'], RDF.type, BRICK.Illumination_Sensor))
            sensors.append((BLDG[name+'_lux'], BF.hasLocation, BLDG[room]))
            sensors.append((BLDG[name+'_lux'], BF.isPointOf, BLDG[room]))

        for triple in sensors:
            self.G.add(triple)

