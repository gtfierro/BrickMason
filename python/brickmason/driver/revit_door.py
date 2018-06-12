from rdflib import Graph, Namespace, URIRef, Literal
import re
import sys
import pandas as pd
from IPython import embed
from xbos.services.brick import Generator

import coloredlogs, logging
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

def clean(s):
    s = str(s)
    s = s.replace(' ','_')
    return s

class Generator(object):
    def __init__(self, G, cfg):
        self.G = G
        filename = cfg['revit_door_schedule']
        BLDG = cfg['BLDG']
        df = pd.read_csv(filename, delimiter='\t', dtype=object)
        for tup in df[df['From Room: Number'].notnull() & df['To Room: Number'].notnull()].iterrows():
            room = tup[1]
            name = 'Room_'+clean(room['From Room: Number'])
            toname = 'Room_'+clean(room['To Room: Number'])

            self.G.add((BLDG[name], RDF.type, BRICK.Room))
            self.G.add((BLDG[toname], RDF.type, BRICK.Room))
            self.G.add((BLDG[name], BF.adjacentTo, BLDG[toname]))
            logging.info("{0} adjacent to {1}".format(name, toname))
