from rdflib import Graph, Namespace, URIRef, Literal
import re
import sys
import pandas as pd
from IPython import embed
from xbos.services.pundat import DataClient
from xbos.services.brick import Generator

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

class Generator(object):
    def __init__(self, cfg):
        #BLDG = Namespace(cfg[
        print opts
