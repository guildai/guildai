import os

def path(subpath):
    return os.path.join(_root(), subpath)

def _root():
    return os.path.expanduser(os.path.join("~", ".guild"))
