from rdflib import Graph, Namespace, URIRef, Literal
from xbos.services.pundat import DataClient
import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s')

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
BRICKFRAME = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')
BF = BRICKFRAME
OWL = Namespace('http://www.w3.org/2002/07/owl#')

class Generator(object):
    def __init__(self, G, cfg):
        BLDG = cfg['BLDG']
        client = DataClient(archivers=[cfg['archiver']])
        for station in cfg['stations']:
            result = client.query('select uuid, path where uri like "nws/weather/{0}" and name = "relative_humidity";'.format(station))
            for doc in result['metadata']:
                name = "weather_{0}_relative_humidity".format(station)
                G.add((BLDG[name], RDF.type, BRICK.Weather_Relative_Humidity_Sensor))
                G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
            result = client.query('select uuid, path where uri like "nws/weather/{0}" and name = "wind_direction";'.format(station))
            for doc in result['metadata']:
                name = "weather_{0}_wind_direction".format(station)
                G.add((BLDG[name], RDF.type, BRICK.Weather_Wind_Direction_Sensor))
                G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
            result = client.query('select uuid, path where uri like "nws/weather/{0}" and name = "wind_speed";'.format(station))
            for doc in result['metadata']:
                name = "weather_{0}_wind_speed".format(station)
                G.add((BLDG[name], RDF.type, BRICK.Weather_Wind_Speed_Sensor))
                G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
            result = client.query('select uuid, path where uri like "nws/weather/{0}" and name = "temperature";'.format(station))
            for doc in result['metadata']:
                name = "weather_{0}_temperature".format(station)
                G.add((BRICK.Weather_Temperature_Sensor, RDF.type, OWL.Class))
                G.add((BRICK.Weather_Temperature_Sensor, RDFS.subClassOf, BRICK.Sensor))
                G.add((BRICK.Weather_Temperature_Sensor, RDFS.subClassOf, BRICK.Weather))
                G.add((BLDG[name], RDF.type, BRICK.Weather_Temperature_Sensor))
                G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
            result = client.query('select uuid, path where uri like "nws/weather/{0}" and name = "cloud_coverage";'.format(station))
            for doc in result['metadata']:
                name = "weather_{0}_cloud_coverage".format(station)
                G.add((BRICK.Weather_Cloud_Coverage_Sensor, RDF.type, OWL.Class))
                G.add((BRICK.Weather_Cloud_Coverage_Sensor, RDFS.subClassOf, BRICK.Sensor))
                G.add((BRICK.Weather_Cloud_Coverage_Sensor, RDFS.subClassOf, BRICK.Weather))
                G.add((BLDG[name], RDF.type, BRICK.Weather_Cloud_Coverage_Sensor))
                G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
            result = client.query('select uuid, path where uri like "nws/weather/{0}" and name = "cloud_height";'.format(station))
            for doc in result['metadata']:
                name = "weather_{0}_cloud_height".format(station)
                G.add((BRICK.Weather_Cloud_Height_Sensor, RDF.type, OWL.Class))
                G.add((BRICK.Weather_Cloud_Height_Sensor, RDFS.subClassOf, BRICK.Sensor))
                G.add((BRICK.Weather_Cloud_Height_Sensor, RDFS.subClassOf, BRICK.Weather))
                G.add((BLDG[name], RDF.type, BRICK.Weather_Cloud_Height_Sensor))
                G.add((BLDG[name], BF.uuid, Literal(doc['uuid'])))
