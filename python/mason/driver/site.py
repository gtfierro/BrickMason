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

class Generator(object):
    def __init__(self, G, cfg):
        BLDG = cfg['BLDG']

        site = BLDG[cfg.get('filename')]
        G.add((site, RDF.type, BRICK.Site))

        human_name = cfg.get('human_name')
        if human_name:
            G.add((site, BF.HumanName, Literal(human_name)))

        zip_code = cfg.get('zip_code')
        if zip_code:
            G.add((site, BF.ZipCode, Literal(zip_code)))

        country = cfg.get('country')
        if country:
            G.add((site, BF.Country, Literal(country)))

        timezone = cfg.get('timezone')
        if timezone:
            G.add((site, BF.Timezone, Literal(timezone)))

        square_feet = cfg.get('square_feet')
        if square_feet:
            G.add((site, BF.AreaSquareFeet, Literal(square_feet)))

        square_meters = cfg.get('square_meters')
        if square_meters:
            G.add((site, BF.AreaSquareMeters, Literal(square_meters)))

        num_floors = cfg.get('num_floors')
        if num_floors:
            G.add((site, BF.NumFloors, Literal(num_floors)))

        primary_function = cfg.get('primary_function')
        if primary_function:
            G.add((site, BF.PrimaryFunction, Literal(primary_function)))

        logging.info("Adding bf:site to all objects...")
        G.bind('rdf', RDF)
        G.bind('owl', OWL)
        q = """PREFIX rdf: <{0}>
PREFIX owl: <{1}>
SELECT DISTINCT ?x WHERE {{ ?x rdf:type/rdf:type owl:Class }}""".format(RDF,OWL)
        res = G.query(q)
        for row in res:
            G.add((row[0], BF.hasSite, site))
