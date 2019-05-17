from rdflib import Graph, Namespace, URIRef, Literal
from collections import defaultdict
import uuid

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
        _g = Graph()
        _g.parse('Brick.ttl', format='turtle')
        _g.parse('BrickFrame.ttl', format='turtle')
        _g.bind('rdf', RDF)
        _g.bind('owl', OWL)
        _g.bind('bf', BRICKFRAME)
        _g += G
        q = """PREFIX rdf: <{0}>
PREFIX owl: <{1}>
PREFIX bf: <{2}>
SELECT DISTINCT ?x ?o WHERE {{ ?x rdf:type ?o. ?x bf:hasSite ?site }}""".format(RDF,OWL, BRICKFRAME)
        print(q)
        res = _g.query(q)
        counters = defaultdict(int)
        names = {}
        sitename = 'site-'+str(uuid.uuid4())
        for row in res:
            # row [0] is the instance, row[1] is the class
            # remove the old row from the database
            G.remove((row[0], RDF.type, row[1]))
            # check if we have an 'anonymous' name for this
            if row[0] in names:
                continue
            counters[row[1]] += 1
            # remove the Brick namespace when we form the new URI
            value = row[1].split('#')[1]
            names[row[0]] = BLDG[value + str(counters[row[1]])]
            G.add((names.get(row[0]), RDF.type, row[1]))

        for row in G:
            newsub = names.get(row[0], row[0])
            newobj = names.get(row[2], row[2])
            G.remove(row)
            if (row[1] == BRICKFRAME.hasSite):
                G.add((newsub, BRICKFRAME.hasSite, BLDG[sitename]))
            elif (row[1] == RDF.type and row[2] == BRICK.Site):
                G.add((newsub, RDF.type, BLDG[sitename]))
            else:
                G.add((newsub, row[1], newobj))

        q = """PREFIX rdf: <{0}>
PREFIX owl: <{1}>
PREFIX bf: <{2}>
SELECT DISTINCT ?x ?site WHERE {{ ?x bf:hasSite ?site }}""".format(RDF,OWL, BRICKFRAME)
        print(q)
        res = _g.query(q)
