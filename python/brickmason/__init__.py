import os
import pytoml
import importlib
import coloredlogs, logging
from ontologies import *

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

__all__ = ['driver','ontologies']

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
    rdfns = config.get('rdf_namespace')
    if rdfns is None:
        logging.error("NEED rdf_namespace")    
        return
    if not rdfns.endswith('#'):
        rdfns += '#'
    BLDG = Namespace(rdfns)
    config['BLDG'] = BLDG
    G.bind('bldg', BLDG)

    extra_section = cfg.pop('extra')

    for name, section in cfg.items():
        scfg = section.pop('config') if 'config' in section else {}
        scfg = merge_config(config, scfg)
        title = "Running section {0}".format(name)
        logger.info('#'*len(title))
        logger.info(title)
        logger.info('#'*len(title))
        for ssname, sscfg in section.items():
            title = "Running subsection {0}.{1}".format(name, ssname)
            logger.info('#'*len(title))
            logger.info(title)
            logger.info('#'*len(title))
            sscfg = merge_config(scfg, sscfg)
            generator = import_string(sscfg['driver'])
            # add triples from generator
            generator(G, sscfg)

    # run extra_section
    logging.info("Running EXTRA section last")
    scfg = extra_section.pop('config') if 'config' in extra_section else {}
    scfg = merge_config(config, scfg)
    logger.info("Running section {0}".format('extra'))
    for ssname, sscfg in extra_section.items():
        logger.info("Running subsection {0}".format(ssname))
        sscfg = merge_config(scfg, sscfg)
        generator = import_string(sscfg['driver'])
        # add triples from generator
        generator(G, sscfg)

    G.serialize(config.get('output','.')+'/'+config['filename'] + '.ttl',format='turtle')
    logging.info("Generated {0} triples!".format(len(G)))
    
