from rdflib import Namespace, URIRef, Literal
from xbos.services.pundat import DataClient
import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BF = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
class Generator(object):
    def __init__(self, G, cfg):
        BLDG = cfg['BLDG']
        subid = cfg['subid']
        uuid = cfg['uuid']

        client = DataClient(archivers=[cfg['archiver']])
        logging.info("Querying for GreenButton")
        result = client.query('select uuid, path where uri like "{subid}/{uuid}"'.format(subid=subid,uuid=uuid))
        for doc in result['metadata']:
            name = "green_button_meter_{0}".format(cfg['namespace'])
            G.add((BLDG[name], RDF.type, BRICK.Green_Button_Meter))
            G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
