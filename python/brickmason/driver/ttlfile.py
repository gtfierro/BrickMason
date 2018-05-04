from rdflib import Graph, Namespace, URIRef, Literal
from xbos.services.pundat import DataClient
import coloredlogs, logging
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')

class Generator(object):
    def __init__(self, G, cfg):
        G.load(cfg['ttlfile'], format='turtle')
