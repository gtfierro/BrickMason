import sys
from collections import defaultdict
from ifcfilereader import *
schema = IfcSchema("IFC2X3_TC1.exp")
f = IfcFile(sys.argv[1], schema)

def parseid(s):
    if isinstance(s, str):
        s = s.replace('#','')
    return int(s)
def fixname(n):
    return n.replace(' ','_')

# zones
_zones = f.entsByName["IFCZONE"]
zones = {}
for zone in _zones:
    z = f.getEntityById(int(zone))
    zones[parseid(z['id'])] = z

# get groups
zone2rooms = defaultdict(list)
_groups = f.entsByName["IFCRELASSIGNSTOGROUP"]
for group in _groups:
    group = f.getEntityById(parseid(group))
    zoneid = parseid(group['attributes'].get('RelatingGroup'))
    zone = zones.get(zoneid)
    #print parseid(group['attributes'].get('RelatingGroup'))
    if zone is None:
        continue
    things = group['attributes'].get('RelatedObjects')
    for thing in things:
        thing = f.getEntityById(parseid(thing))
        if thing['name'] == 'IFCSPACE':
            #print 'room', thing
            longname = thing['attributes']['LongName']
            name = thing['attributes']['Name']
            zone2rooms[zoneid].append(longname+name)

_groups = f.entsByName["IFCRELAGGREGATES"]
for group in _groups:
    group = f.getEntityById(parseid(group))
    relating_obj_id = parseid(group['attributes']['RelatingObject'])
    print f.getEntityById(relating_obj_id)['name']

floors = {}
_groups = f.entsByName["IFCBUILDINGSTOREY"]
for group in _groups:
    group = f.getEntityById(parseid(group))
    print group
    floors[parseid(group['id'])] = group['attributes']['LongName']
    continue
    relating_obj_id = parseid(group['attributes']['RelatingObject'])
    print f.getEntityById(relating_obj_id)['name']

rooms = []
rooms2floors = defaultdict(list)
_groups = f.entsByName["IFCRELAGGREGATES"]
for group in _groups:
    group = f.getEntityById(parseid(group))
    relating_obj_id = parseid(group['attributes']['RelatingObject'])
    ent = f.getEntityById(relating_obj_id)
    if ent['name'] == 'IFCBUILDINGSTOREY':
        for oid in group['attributes']['RelatedObjects']:
            o = f.getEntityById(parseid(oid))
            room = o['attributes']['LongName']+o['attributes']['Name']
            rooms.append(room)
            rooms2floors[ent['attributes']['LongName']].append(room)

from rdflib import Graph, Namespace, URIRef, Literal
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
BF = BRICKFRAME
OWL = Namespace('http://www.w3.org/2002/07/owl#')
BLDG = Namespace('http://buildsys.org/ontologies/bldg#')

g = Graph()
g.bind('rdf', RDF)
g.bind('rdfs', RDFS)
g.bind('brick', BRICK)
g.bind('bf', BRICKFRAME)
g.bind('bldg', BLDG)

for rm in rooms:
    rm = fixname(rm)
    g.add((BLDG[rm], RDF.type, BRICK.Room))
for floor in floors.values():
    floor = fixname(floor)
    g.add((BLDG[floor], RDF.type, BRICK.Floor))
for floor, roomlist in rooms2floors.items():
    floor = fixname(floor)
    for room in roomlist:
        room = fixname(room)
        g.add((BLDG[floor], BF.hasPart, BLDG[room]))
for zone, roomlist in zone2rooms.items():
    zone = fixname(str(zone))
    g.add((BLDG[zone], RDF.type, BRICK.HVAC_ZONE))
    for room in roomlist:
        room = fixname(room)
        g.add((BLDG[room], BF.isPartOf, BLDG[zone]))

g.serialize('building.ttl',format='turtle')
