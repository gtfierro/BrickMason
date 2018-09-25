from rdflib import Graph, Namespace, URIRef, Literal
from collections import defaultdict

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
        for row in res:
            #print(row)
            G.remove((row[0], RDF.type, row[1]))
            if row[0] in names:
                continue
            counters[row[1]] += 1
            names[row[0]] = row[1] + str(counters[row[1]])
            G.add((names.get(row[0]), RDF.type, row[1]))

        for row in G:
            newsub = names.get(row[0], row[0])
            newobj = names.get(row[2], row[2])
            G.remove(row)
            G.add((newsub, row[1], newobj))
