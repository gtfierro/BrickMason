from rdflib import Graph, Namespace, URIRef, Literal
from collections import defaultdict
from .pythonifc.ifcfilereader import *
import coloredlogs, logging
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
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

        _g = Graph()
        _g.parse('Brick.ttl', format='turtle')
        _g.parse('BrickFrame.ttl', format='turtle')
        _g.bind('rdf', RDF)
        _g.bind('owl', OWL)
        _g += G
        

        q = """PREFIX rdf: <{0}>
PREFIX owl: <{1}>
SELECT DISTINCT ?x ?class WHERE {{ ?x rdf:type/rdf:type owl:Class . ?x rdf:type ?class }}""".format(RDF,OWL)
        res = _g.query(q)
        for row in res:
            if row[1].split('#')[-1] == 'Site':
                continue
            G.add((row[0], BF.hasSite, site))
