from rdflib import Graph, Namespace, URIRef, Literal
import re
import sys
import pandas as pd
from IPython import embed

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
BF = BRICKFRAME
OWL = Namespace('http://www.w3.org/2002/07/owl#')
BLDG = Namespace('http://buildsys.org/ontologies/bldg#')


def clean(s):
    s = str(s)
    s = s.replace(' ','_')
    return s

def parse(filename):
    g = Graph()
    g.bind('rdf', RDF)
    g.bind('rdfs', RDFS)
    g.bind('brick', BRICK)
    g.bind('bf', BRICKFRAME)
    g.bind('bldg', BLDG)

    df = pd.read_csv(filename, delimiter='\t')
    print df.columns

    # add rooms + floors
    print 'Adding Rooms and Floors'
    for tup in df[df['Room: Number'].notnull()].iterrows():
        room = tup[1]
        name = clean(room['Room: Number'])
        floor = clean(room['Level'])
        zone = str(room['Space: Zone']).replace(' ','_')
        #zone = re.search(r'(\d+)', str(room['Space: Zone']))

        # add floor and room
        g.add((BLDG[name], RDF.type, BRICK.Room))
        g.add((BLDG[floor], RDF.type, BRICK.Floor))
        g.add((BLDG[floor], RDF.label, Literal(room['Level'])))
        g.add((BLDG[floor], BF.hasPart, BLDG[name]))
        g.add((BLDG[name], RDF.label, Literal(room['Room: Name'])))

        # link room to HVAC zone
        if not zone:
            print 'No Zone information found'
            continue
        zonename = 'HVAC_Zone_'+zone
        g.add((BLDG[name], BF.isPartOf, BLDG[zonename]))
        g.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))

    # add hvac zones
    zones = df['Space: Zone'].unique()
    print 'Listing HVAC zones'
    for zone in zones:
        print 'zone>', zone

    # add lights
    print 'Adding lighting fixtures'
    fixtures = df[df['Category'] == 'Lighting Fixtures']
    for fixture in fixtures.iterrows():
        if fixture[1]['Mark'] and 'Sensor' in str(fixture[1]['Mark']):
            name = clean(fixture[1]['Mark'])
            room = clean(fixture[1]['Room: Number'])
            zone = str(fixture[1]['Space: Zone']).replace(' ','_')
            # add lighting and link to room
            g.add((BLDG[name], RDF.type, BRICK.Lighting_System))
            g.add((BLDG[name], RDF.label, Literal(fixture[1]['Mark'])))
            g.add((BLDG[name], BF.feeds, BLDG[room]))
            g.add((BLDG[name], BF.isLocatedIn, BLDG[room]))
            if not zone:
                print 'No Zone information found'
                continue
            zonename = 'HVAC_Zone_'+zone
            g.add((BLDG[room], BF.isPartOf, BLDG[zonename]))

    # add dampers
    print 'Adding dampers'
    for item in df[df['Category'] == 'Air Terminals'].iterrows():
        item = item[1]
        print 'adding damper', item
        room = clean(item['Room: Number'])
        if item['Family'] == 'Return Diffuser':
            dmp_id = 'return_damper_' + str(item['Mark'])
            g.add((BLDG[dmp_id], RDF.type, BRICK.Return_Air_Damper))
            g.add((BLDG[dmp_id], BF.isFedBy, BLDG[room]))
        if item['Family'] == 'Supply Diffuser':
            dmp_id = 'supply_damper_' + str(item['Mark'])
            g.add((BLDG[dmp_id], RDF.type, BRICK.Supply_Air_Damper))
            g.add((BLDG[dmp_id], BF.feeds, BLDG[room]))

    # add RTUs + Zones
    print 'Adding RTus and zones'
    for item in df[(df['Category'].astype('str') == 'Mechanical Equipment') & (df['Type Mark'].astype('str') == 'RTU')].iterrows():
        item = item[1]
        #zone = re.search(r'(\d+)', item['Mark'])
        zone = str(item['Mark']).replace(' ','_')

        # add RTU
        rtuname = 'RTU_'+zone
        g.add((BLDG[rtuname], RDF.type, BRICK.Rooftop_Unit))

        if not zone:
            print 'no zones found'
            continue
        zonename = 'HVAC_Zone_'+zone
        g.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))
        g.add((BLDG[rtuname], BF.feeds, BLDG[zonename]))

    # add thermostats
    print 'Adding thermostat'
    for item in df[(df['Family'] == 'Thermostat_573')].iterrows():
        item = item[1]
        print item
        #zone = re.search(r'(\d+)', str(item['Space: Zone']))
        zone = str(item['Space: Zone']).replace(' ','_')
        if not zone:
            print 'No Zone information'
            continue
        zonename = 'HVAC_Zone_'+zone
        tstatname = 'thermostat_' + zonename
        rtuname = 'RTU_'+zonename
        roomname = clean(item['Room: Number'])
        g.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))
        g.add((BLDG[tstatname], RDF.type, BRICK.Thermostat))
        g.add((BLDG[tstatname], BF.controls, BLDG[rtuname]))
        g.add((BLDG[tstatname], BF.isLocatedIn, BLDG[roomname]))

    print len(g)
    return g

if __name__ == '__main__':
    g = parse(sys.argv[1])
    name = '.'.join(sys.argv[1].split('.')[:-1])
    g.serialize(name+'.ttl',format='turtle')
