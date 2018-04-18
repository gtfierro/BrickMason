from rdflib import Graph, Namespace, URIRef, Literal
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')


g = Graph()
g.bind('rdf', RDF)
g.bind('rdfs', RDFS)
g.bind('brick', BRICK)
g.bind('bf', BRICKFRAME)

g.add((BRICK.Green_Button_Meter, RDF.type, OWL.Class))
g.add((BRICK.Green_Button_Meter, RDFS.subClassOf, BRICK.Building_Electric_Meter))

g.add((BRICK.Building_Electric_Meter, RDF.type, OWL.Class))
g.add((BRICK.Building_Electric_Meter, RDFS.subClassOf, BRICK.Electric_Meter))

g.add((BRICK.RTU, RDFS.subClassOf, BRICK.AHU))
g.add((BRICK.RTU, RDF.type, OWL.Class))

g.add((BRICK.Illumination_Sensor, RDFS.subClassOf, BRICK.Sensor))
g.add((BRICK.Illumination_Sensor, RDF.type, OWL.Class))

g.add((BRICK.Site, RDFS.subClassOf, BRICK.Location))
g.add((BRICK.Site, RDF.type, OWL.Class))

# add properties for sites
g.add((BRICKFRAME.HumanName, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.HumanName, RDFS.range, BRICKFRAME.Label))

g.add((BRICKFRAME.ZipCode, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.ZipCode, RDFS.range, BRICKFRAME.Label))

g.add((BRICKFRAME.Timezone, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.Timezone, RDFS.range, BRICKFRAME.Label))

g.add((BRICKFRAME.AreaSquareFeet, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.AreaSquareFeet, RDFS.range, BRICKFRAME.Label))

g.add((BRICKFRAME.AreaSquareMeters, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.AreaSquareMeters, RDFS.range, BRICKFRAME.Label))

g.add((BRICKFRAME.NumFloors, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.NumFloors, RDFS.range, BRICKFRAME.Label))

g.add((BRICKFRAME.PrimaryFunction, RDF.type, OWL.ObjectProperty))
g.add((BRICKFRAME.PrimaryFunction, RDFS.range, BRICKFRAME.Label))

g.serialize('extra_classes.ttl',format='turtle')
