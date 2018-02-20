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
    for tup in df[df['Room: Number'].notnull()].iterrows():
        room = tup[1]
        name = clean(room['Room: Number'])
        floor = clean(room['Level'])
        zone = re.search(r'(\d+)', room['Space: Zone'])
        if not zone: continue
        zonename = 'HVAC_Zone_'+str(int(zone.groups()[0]))
        g.add((BLDG[name], RDF.type, BRICK.Room))
        g.add((BLDG[floor], RDF.type, BRICK.Floor))
        g.add((BLDG[floor], RDF.label, Literal(room['Level'])))
        g.add((BLDG[floor], BF.hasPart, BLDG[name]))
        g.add((BLDG[name], BF.isPartOf, BLDG[zonename]))
        g.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))
        g.add((BLDG[name], RDF.label, Literal(room['Room: Name'])))

    # add hvac zones
    zones = df['Space: Zone'].unique()
    for zone in zones:
        print zone

    # add lights
    fixtures = df[df['Category'] == 'Lighting Fixtures']
    for fixture in fixtures.iterrows():
        if fixture[1]['Mark'] and 'Sensor' in fixture[1]['Mark']:
            name = clean(fixture[1]['Mark'])
            room = clean(fixture[1]['Room: Number'])
            zone = re.search(r'(\d+)', fixture[1]['Space: Zone'])
            print fixture[1]['Space: Zone']
            if not zone: continue
            zonename = 'HVAC_Zone_'+str(int(zone.groups()[0]))
            g.add((BLDG[name], RDF.type, BRICK.Lighting_System))
            g.add((BLDG[name], RDF.label, Literal(fixture[1]['Mark'])))
            g.add((BLDG[name], BF.feeds, BLDG[room]))
            g.add((BLDG[room], BF.isPartOf, BLDG[zonename]))
            g.add((BLDG[name], BF.isLocatedIn, BLDG[room]))

    # add dampers
    for item in df[df['Category'] == 'Air Terminals'].iterrows():
        item = item[1]
        room = clean(item['Room: Number'])
        if item['Family'] == 'Return Diffuser':
            dmp_id = 'return_damper_' + item['Mark']
            g.add((BLDG[dmp_id], RDF.type, BRICK.Return_Air_Damper))
            g.add((BLDG[dmp_id], BF.isFedBy, BLDG[room]))
        if item['Family'] == 'Supply Diffuser':
            dmp_id = 'supply_damper_' + item['Mark']
            g.add((BLDG[dmp_id], RDF.type, BRICK.Supply_Air_Damper))
            g.add((BLDG[dmp_id], BF.feeds, BLDG[room]))
        
    # add RTUs + Zones
    for item in df[(df['Category'].astype('str') == 'Mechanical Equipment') & (df['Type Mark'].astype('str') == 'RTU')].iterrows():
        item = item[1]
        zone = re.search(r'(\d+)', item['Mark'])
        print item
        if not zone: continue
        zonename = 'HVAC_Zone_'+zone.groups()[0]
        rtuname = 'RTU_'+zone.groups()[0]
        g.add((BLDG[zonename], RDF.type, BRICK.HVAC_Zone))
        g.add((BLDG[rtuname], RDF.type, BRICK.Rooftop_Unit))
        g.add((BLDG[rtuname], BF.feeds, BLDG[zonename]))

    # add thermostats
    for item in df[(df['Family'] == 'Thermostat_573')].iterrows():
        item = item[1]
        zone = re.search(r'(\d+)', item['Space: Zone'])
        if not zone: continue
        zonename = 'HVAC_Zone_'+str(int(zone.groups()[0]))
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
