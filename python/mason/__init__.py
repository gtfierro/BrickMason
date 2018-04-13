import pytoml
import importlib

__all__ = ['driver','driver.revit']

def import_string(name):
    mod = importlib.import_module(name)
    return getattr(mod, 'Generator')

def load_config(cfgfile):
    return pytoml.load(open(cfgfile))

def execute(cfg):
    print cfg
