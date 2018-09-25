from rdflib import Graph, Namespace, URIRef, Literal
import re
import sys
import json
from IPython import embed
from xbos.services.brick import Generator

import coloredlogs, logging
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

class Generator(object):
    def __init__(self, G, cfg):
        self.G = G
        BLDG = cfg['BLDG']
        tree = json.load(open(cfg['filename']))
        for equip in tree['objects']:
            equipment_name = equip['name']
            equipment_type = URIRef(equip['type'])

            G.add((BLDG[equipment_name], RDF.type, equipment_type))

            for point in equip['points']:
                equipment_point_name = equipment_name+'.'+point['name']
                equipment_point_type = URIRef(point['type'])

                G.add((BLDG[equipment_name], BF.hasPoint, BLDG[equipment_point_name]))
                G.add((BLDG[equipment_point_name], RDF.type, equipment_point_type))
                G.add((BLDG[equipment_point_name], BF.pointname, Literal(point['fullname'])))

            for part in equip['parts']:
                equipment_part_name = equipment_name+'.'+part['name']
                equipment_part_type = URIRef(part['type'])

                G.add((BLDG[equipment_name], BF.hasPart, BLDG[equipment_part_name]))
                G.add((BLDG[equipment_part_name], RDF.type, equipment_part_type))

                for ppoint in part['points']:
                    part_point_name = equipment_part_name+'.'+ppoint['name']
                    part_point_type = URIRef(ppoint['type'])

                    G.add((BLDG[equipment_part_name], BF.hasPoint, BLDG[part_point_name]))
                    G.add((BLDG[part_point_name], BF.pointname, Literal(ppoint['fullname'])))
                    G.add((BLDG[part_point_name], RDF.type, part_point_type))
        #embed()
