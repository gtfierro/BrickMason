import os
import pytoml
import importlib
import coloredlogs, logging

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

__all__ = ['driver','driver.revit']

def import_string(name):
    mod = importlib.import_module(name)
    return getattr(mod, 'Generator')

def load_config(cfgfile):
    return pytoml.load(open(cfgfile))

def merge_config(globalcfg, localcfg):
    cfg = globalcfg.copy()
    for k,v in localcfg.items():
        cfg[k] = v
    return cfg

from rdflib import Graph, Namespace, URIRef, Literal

def execute(cfg):
    RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
    BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
    BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
    BF = BRICKFRAME
    OWL = Namespace('http://www.w3.org/2002/07/owl#')
    G = Graph()
    G.bind('rdf', RDF)
    G.bind('rdfs', RDFS)
    G.bind('brick', BRICK)
    G.bind('bf', BRICKFRAME)

    # global config
    config = cfg.pop('config')

    # configure output dir
    output_dir = config.get('output')
    if output_dir and not os.path.exists(output_dir):
        logging.info("Making output directory {0}".format(output_dir))
        os.mkdir(output_dir)

    # configure BLDG namespace
    BLDG = Namespace('http://xbos.io/ontologies/{0}#'.format(config['namespace']))
    config['BLDG'] = BLDG
    G.bind('bldg', BLDG)
    # add extra classes
    if config.get('extra_classes'):
        #TODO: add!
        G.load(config['extra_classes'],format='turtle')

    for name, section in cfg.items():
        scfg = section.pop('config')
        scfg = merge_config(config, scfg)
        logger.info("Running section {0}".format(name))
        for ssname, sscfg in section.items():
            logger.info("Running subsection {0}.{1}".format(name, ssname))
            sscfg = merge_config(scfg, sscfg)
            generator = import_string(sscfg['driver'])
            # add triples from generator
            generator(G, sscfg)

    G.serialize(config.get('output','.')+'/'+config['namespace'] + '.ttl',format='turtle')
    print len(G)
    
