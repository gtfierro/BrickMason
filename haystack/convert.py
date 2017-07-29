from rdflib import Graph, Namespace, URIRef, Literal
import sys
import rdflib
import pandas as pd
import json
import re

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
BF = BRICKFRAME
OWL = Namespace('http://www.w3.org/2002/07/owl#')
BLDG = Namespace('http://buildsys.org/ontologies/bldg#')

g = rdflib.Graph()
g.bind('rdf', RDF)
g.bind('rdfs', RDFS)
g.bind('brick', BRICK)
g.bind('bf', BRICKFRAME)
g.bind('bldg', BLDG)

if len(sys.argv) > 1: siteref = sys.argv[1]
else: siteref = 'Ghausi'

ahu_filename = 'ahu.json'
ahus = json.load(open(ahu_filename))
ahus = [ahu for ahu in ahus if ahu['siteRef'] == siteref]

vav_filename = 'vav.json'
vavs = json.load(open(vav_filename))
vavs = [vav for vav in vavs if vav['siteRef'] == siteref]

points = pd.read_csv('points.csv')
points = points[points['siteRef'].str.split(" ").str[1] == '"'+siteref+'"']

def instantiate_ahu(doc):
    triples = []
    if not doc['ahu']:
        return triples
    name = fix(doc['id'])
    triples.append((BLDG[name], RDF.type, BRICK.AHU))

    return triples

def instantiate_vav(doc):
    triples = []
    if not doc['vav']:
        return triples
    vavname = fix(doc['id'])
    if vavname is None:
        print doc
        sys.exit(1)
    zonename = vavname+"_zone"
    ahuname = fix(doc['equipRef'])
    triples.append((BLDG[vavname], RDF.type, BRICK.VAV))
    triples.append((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))

    triples.append((BLDG[vavname], BF.isFedBy, BLDG[ahuname]))
    triples.append((BLDG[vavname], BF.feeds, BLDG[zonename]))

    if doc['reheat'] != 'nan':
        rh_valve = vavname+"_rh_vlv"
        triples.append((BLDG[rh_valve], RDF.type, BRICK.Reheat_Valve))
        triples.append((BLDG[vavname], BF.hasPart, BLDG[rh_valve]))

    # add rooms
    rooms = [fix(parse_room(doc['id']))]
    other_rooms = map(lambda x: fix(x.strip()), str(doc['associatedRooms']).split(','))
    if other_rooms[0] != 'nan':
        rooms.extend(other_rooms)
    for room in rooms:
        triples.append((BLDG[room], RDF.type, BRICK.Room))
        triples.append((BLDG[room], BF.isPartOf, BLDG[zonename]))

    # add floors (rooms first digit is the floor)
    for room in rooms:
        digits = re.findall(r'\d',room)
        if len(digits) == 0: continue
        floor = digits[0]
        floorname = 'floor_'+floor
        triples.append((BLDG[floorname], RDF.type, BRICK.Floor))
        triples.append((BLDG[floorname], BF.hasPart, BLDG[room]))

    # assume that first room is where the damper is (its encoded in the name of the vav)
    damper_room = rooms[0]
    dampername = vavname+"_damper"
    triples.append((BLDG[dampername], RDF.type, BRICK.Damper))
    triples.append((BLDG[vavname], BF.hasPart, BLDG[dampername]))
    triples.append((BLDG[dampername], BF.isLocatedIn, BLDG[damper_room]))

    return triples

sensortags = [
    {'sensor','discharge','air','temp'},
    {'sensor','return','air','temp'},
    {'sensor','outside','air','temp'},
    {'sensor','supply','air','temp'},
    {'sensor','zone.1','air','temp'},
    {'sensor','air','temp'},
    {'sensor','temp'},

    {'sensor','discharge','air','flow'},
    {'sensor','return','air','flow'},
    {'sensor','supply','air','flow'},
    {'sensor','zone.1','air','flow'},
    {'sensor','air','flow'},

    {'sensor','discharge','air','pressure'},
    {'sensor','return','air','pressure'},
    {'sensor','supply','air','pressure'},
    {'sensor','zone.1','air','pressure'},
    {'sensor','air','pressure'},

    {'sensor','energy'},

    {'sensor','occ','status'},

    {'sensor','power'},
    {'sensor','speed'},

]

sensortypes = [
    BRICK.Discharge_Air_Temperature_Sensor,
    BRICK.Return_Air_Temperature_Sensor,
    BRICK.Outside_Air_Temperature_Sensor,
    BRICK.Supply_Air_Temperature_Sensor,
    BRICK.Zone_Air_Temperature_Sensor,
    BRICK.Air_Temperature_Sensor,
    BRICK.Temperature_Sensor,

    BRICK.Discharge_Air_Flow_Sensor,
    BRICK.Return_Air_Flow_Sensor,
    BRICK.Supply_Air_Flow_Sensor,
    BRICK.Zone_Air_Flow_Sensor,
    BRICK.Air_Flow_Sensor,

    BRICK.Discharge_Air_pressure_Sensor,
    BRICK.Return_Air_pressure_Sensor,
    BRICK.Supply_Air_pressure_Sensor,
    BRICK.Zone_Air_pressure_Sensor,
    BRICK.Air_pressure_Sensor,

    BRICK.Electric_Meter,
    BRICK.Occupancy_Sensor,
    BRICK.Power_Meter,
    BRICK.Speed_Sensor,

]

sptags = [
    {'sp', 'temp', 'air', 'heat', 'unocc'},
    {'sp', 'temp', 'air', 'cool', 'unocc'},
    {'sp', 'temp', 'air', 'heat', 'occ'},
    {'sp', 'temp', 'air', 'cool', 'occ'},
    {'sp', 'temp', 'air', 'heat'},
    {'sp', 'temp', 'air', 'cool'},
    {'sp', 'temp', 'air', 'mixed'},
    {'sp', 'temp', 'air', 'supply'},
    {'sp', 'temp', 'air', 'discharge'},
    {'sp', 'temp', 'air', 'zone.1'},
    {'sp', 'air', 'mixed'},

    {'sp', 'air', 'flow', 'discharge'},
    {'sp', 'air', 'flow', 'supply'},
    {'sp', 'air', 'flow', 'differential','unocc'},
    {'sp', 'air', 'flow', 'differential','occ'},
    {'sp', 'air', 'flow', 'differential'},
    {'sp', 'air', 'flow', 'exhaust', 'spMin'},
    {'sp', 'air', 'flow', 'exhaust', 'spMax'},
    {'sp', 'air', 'flow', 'exhaust'},
    {'sp', 'air', 'flow', 'spMin'},
    {'sp', 'air', 'flow', 'spMax'},

    {'sp', 'air', 'pressure', 'discharge'},

    {'sp', 'cmd', 'air', 'damper', 'position'},

    {'sp', 'cmd', 'valve', 'cool', 'position'},
    {'sp', 'cmd', 'valve', 'heat', 'position'},
    {'sp', 'cmd', 'air', 'fan', 'speed'},
]
sptypes = [
    BRICK.VAV_Unoccupied_Heating_Temperature_Setpoint,
    BRICK.VAV_Unoccupied_Cooling_Temperature_Setpoint,
    BRICK.VAV_Occupied_Heating_Temperature_Setpoint,
    BRICK.VAV_Occupied_Cooling_Temperature_Setpoint,
    BRICK.VAV_Heating_Temperature_Setpoint,
    BRICK.VAV_Cooling_Temperature_Setpoint,
    BRICK.Mixed_Air_Temperature_Setpoint,
    BRICK.Supply_Air_Temperature_Setpoint,
    BRICK.Supply_Air_Temperature_Setpoint,
    BRICK.Zone_Air_Temperature_Setpoint,
    BRICK.Mixed_Air_Setpoint,

    BRICK.VAV_Discharge_Air_Flow_Setpoint,
    BRICK.VAV_Supply_Air_Flow_Setpoint,
    BRICK.VAV_Unoccupied_Air_Flow_Differential_Setpoint,
    BRICK.VAV_Occupied_Air_Flow_Differential_Setpoint,
    BRICK.VAV_Air_Flow_Differential_Setpoint,
    BRICK.VAV_Exhaust_Air_Flow_Min_Setpoint,
    BRICK.VAV_Exhaust_Air_Flow_Max_Setpoint,
    BRICK.VAV_Exhaust_Air_Flow_Setpoint,
    BRICK.VAV_Air_Flow_Min_Setpoint,
    BRICK.VAV_Air_Flow_Max_Setpoint,

    BRICK.Discharge_Air_Static_Pressure_Setpoint,

    BRICK.VAV_Damper_Position_Command,

    BRICK.Cooling_Valve_Command,
    BRICK.Heating_Valve_Command,
    BRICK.AHU_Supply_Fan_VFD_Speed_Command,
]

def get_sensors():
    triples = []
    print len(points)
    sensors = points[(points['sensor'].notnull())]
    print len(sensors)
    for row in sensors.iterrows():
        row = row[1] # get the actual Series
        tags = set(row[row=='M'].keys())
        a = False
        for idx, ts in enumerate(sensortags):
            if ts.intersection(tags) == ts:
                kls = sensortypes[idx]
                sensorname = fix(row['id'])
                if sensorname is None:
                    print row['id']
                    sys.exit(1)
                triples.append((BLDG[sensorname], RDF.type, kls))
                if 'Rm' in doc['id']:
                    roomname = fix(parse_room(doc['id']))
                    if 'occ' in tags:
                        triples.append((BLDG[sensorname], BF.isLocatedIn, BLDG[roomname]))
                    else:
                        triples.append((BLDG[sensorname], BF.isPointOf, BLDG[roomname]))

                equipname = fix(row['equipRef']) 
                if equipname is None:
                    continue
                triples.append((BLDG[sensorname], BF.isPointOf, BLDG[equipname]))
                if 'power' in tags:
                    triples.append((BLDG[sensorname], BF.measures, BLDG[equipname]))
                a = True
                break
        if not a:
            if 'sp' in tags:
                print tags
                print row[row.notnull()]
            #print tags, fix(row['id'])
    return triples

def get_setpoints():
    triples = []
    print len(points)
    setpoints = points[(points['sp'].notnull())]
    print len(setpoints)
    for row in setpoints.iterrows():
        row = row[1] # get the actual Series
        tags = set(row[row=='M'].keys())
        a = False
        for idx, ts in enumerate(sptags):
            if ts.intersection(tags) == ts:
                kls = sptypes[idx]
                sensorname = fix(row['id'])
                triples.append((BLDG[sensorname], RDF.type, kls))
                if 'Rm' in doc['id']:
                    roomname = fix(parse_room(doc['id']))
                    if 'occ' in tags:
                        triples.append((BLDG[sensorname], BF.isLocatedIn, BLDG[roomname]))
                    else:
                        triples.append((BLDG[sensorname], BF.isPointOf, BLDG[roomname]))
                equipname = fix(row['equipRef']) 
                if equipname is None:
                    continue
                triples.append((BLDG[sensorname], BF.controls, BLDG[equipname]))
                a = True
                break
        if not a:
            #if 'sp' in tags:
            #    print tags
            #    print row[row.notnull()]
            print tags, fix(row['id'])
    return triples



def fix(s):
    if not (isinstance(s, str) or isinstance(s, unicode)):
        print type(s)
        return None
    if '\$' in s:
        s = s.replace('\$','')
    if s.startswith('@'):
        s = ' '.join(s.split(' ')[1:])[1:-1]
    return s.replace(' ','_')


def parse_room(s):
    idx = s.find('Rm ')
    roomnum = s[idx+3:]
    return 'Room_'+roomnum

alltriples = []
# handle AHUs
for doc in ahus:
    alltriples.extend(instantiate_ahu(doc))
# handle VAVs
for doc in vavs:
    alltriples.extend(instantiate_vav(doc))
# handle sensors
alltriples.extend(get_sensors())
# handle setpoints
alltriples.extend(get_setpoints())



for t in alltriples:
    g.add(t)
g.serialize('{0}.ttl'.format(siteref),format='turtle')

print len(g)
