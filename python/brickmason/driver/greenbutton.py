from rdflib import Namespace, URIRef, Literal
from xbos.services.pundat import DataClient
import coloredlogs, logging
import hashlib
import base64
import uuid as uuidlib
from ..ontologies import *
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
class Generator(object):
    def __init__(self, G, cfg):
        BLDG = cfg['BLDG']
        subid = cfg['subid']
        uuid = cfg['uuid']
        self.namespace = cfg['namespace']
        ns_uuid = uuidlib.UUID(cfg['namespace_uuid'])

        client = DataClient(archivers=[cfg['archiver']])
        logging.info("Querying for GreenButton")

        uri = 'xbos/sharemydata/s.sharemydata/{0}/{1}/Wh/i.sharemydata'.format(subid, uuid)
        pointuuid = uuidlib.uuid3(ns_uuid, str('xbos/sharemydata/{0}/{1}/data'.format(subid, uuid)) + 'wh_value')

        h = hashlib.sha1()
        h.update(str(subid).encode('utf-8'))
        h.update(str(uuid).encode('utf-8'))
        name = 'green_button_meter_{0}'.format(base64.encodestring(h.digest()).strip())

        G.add((BLDG[name], RDF.type, BRICK.Green_Button_Meter))
        G.add((BLDG[name], BF.uuid, Literal(pointuuid)))
        G.add((BLDG[name], BF.uri, Literal(uri)))

        #result = client.query('select uuid, path where uri like "{subid}/{uuid}"'.format(subid=subid,uuid=uuid))
        #for doc in result['metadata']:
        #    name = "green_button_meter_{0}".format(cfg['namespace'])
