from rdflib import Graph, Namespace, URIRef, Literal
from collections import defaultdict
from .pythonifc.ifcfilereader import *
import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
BF = BRICKFRAME
OWL = Namespace('http://www.w3.org/2002/07/owl#')

def parseid(s):
    if isinstance(s, str):
        s = s.replace('#','')
    return int(s)
def fixname(n):
    if n is None:
        return ''
    return n.replace(' ','_')

class Generator(object):
    def __init__(self, G, cfg):
        self.G = G
        schema = IfcSchema(cfg['ifc_schema'])
        ifc_file = IfcFile(cfg['ifc_file'], schema)
        BLDG = cfg['BLDG']

        # zones
        logging.info("Read HVAC zones")
        _zones = ifc_file.entsByName["IFCZONE"]
        zones = {}
        for zone in _zones:
            z = ifc_file.getEntityById(int(zone))
            zones[parseid(z['id'])] = z

        # get groups
        logging.info("Read rooms, map to HVAC zones")
        zone2rooms = defaultdict(list)
        _groups = ifc_file.entsByName["IFCRELASSIGNSTOGROUP"]
        for group in _groups:
            group = ifc_file.getEntityById(parseid(group))
            zoneid = parseid(group['attributes'].get('RelatingGroup'))
            zone = zones.get(zoneid)
            if zone is None:
                logging.warning("No zone found for group")
                continue
            things = group['attributes'].get('RelatedObjects')
            for thing in things:
                thing = ifc_file.getEntityById(parseid(thing))
                if thing['name'] == 'IFCSPACE':
                    longname = thing['attributes']['LongName']
                    name = thing['attributes']['Name']
                    zone2rooms[zoneid].append(longname+name)

        _groups = ifc_file.entsByName["IFCRELAGGREGATES"]
        for group in _groups:
            group = ifc_file.getEntityById(parseid(group))
            relating_obj_id = parseid(group['attributes']['RelatingObject'])

        logging.info("Read building floors")
        floors = {}
        _groups = ifc_file.entsByName["IFCBUILDINGSTOREY"]
        for group in _groups:
            group = ifc_file.getEntityById(parseid(group))
            floors[parseid(group['id'])] = group['attributes']['LongName']

        logging.info("Read rooms")
        rooms = []
        rooms2floors = defaultdict(list)
        _groups = ifc_file.entsByName["IFCRELAGGREGATES"]
        for group in _groups:
            group = ifc_file.getEntityById(parseid(group))
            relating_obj_id = parseid(group['attributes']['RelatingObject'])
            ent = ifc_file.getEntityById(relating_obj_id)
            if ent['name'] == 'IFCBUILDINGSTOREY':
                for oid in group['attributes']['RelatedObjects']:
                    o = ifc_file.getEntityById(parseid(oid))
                    room = o['attributes']['LongName']+o['attributes']['Name']
                    rooms.append(room)
                    rooms2floors[ent['attributes']['LongName']].append(room)

        for rm in rooms:
            rm = fixname(rm)
            G.add((BLDG[rm], RDF.type, BRICK.Room))
        for floor in floors.values():
            floor = fixname(floor)
            G.add((BLDG[floor], RDF.type, BRICK.Floor))
        for floor, roomlist in rooms2floors.items():
            floor = fixname(floor)
            for room in roomlist:
                room = fixname(room)
                G.add((BLDG[floor], BF.hasPart, BLDG[room]))
        for zone, roomlist in zone2rooms.items():
            zone = fixname(str(zone))
            G.add((BLDG[zone], RDF.type, BRICK.HVAC_ZONE))
            for room in roomlist:
                room = fixname(room)
                G.add((BLDG[room], BF.isPartOf, BLDG[zone]))
