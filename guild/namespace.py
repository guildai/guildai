import importlib

__namespace_classes__ = {
    "gpkg": "guild.namespace.gpkg",
    "pypi": "guild.namespace.pypi",
}

__namespaces__ = {}

DEFAULT_NAMESPACE = "gpkg"

class Namespace(object):

    name = None

    def python_project(_self, _val):
        raise NotImplementedException()

    def index_install_urls(_self):
        raise NotImplementedException()

    def index_search_urls(_self):
        raise NotImplementedException()

class pypi(Namespace):

    INDEX_INSTALL_URL = "https://https://pypi.python.org/simple"
    INDEX_SEARCH_URL = "https://pypi.python.org/pypi"

    @staticmethod
    def python_project(val):
        return val

    def index_install_urls(self):
        return [self.INDEX_INSTALL_URL]

    def index_search_urls(self):
        return [self.INDEX_SEARCH_URL]

class gpkg(pypi):

    @staticmethod
    def python_project(val):
        return "gpkg." + val

def init_namespaces():
    """Called by system to initialize the list of available namespaces.

    This function must be called prior to using `iter_namespaces` or
    `for_name`.
    """
    # As there's no overhead in creating any of the namespaces here,
    # we preemptively create them in init. If at any point we open
    # this up to custom namespaces, or any of our namespaces perform
    # work during init, we need to be lazy with our init here (see
    # e.g. guild.plugin.init_plugins).
    for name, cls in __namespace_classes__.items():
        __namespaces__[name] = _init_namespace(cls, name)

def _init_namespace(class_name, name):
    mod_name, class_attr = class_name.rsplit(".", 1)
    ns_mod = importlib.import_module(mod_name)
    ns_class = getattr(ns_mod, class_attr)
    ns = ns_class()
    ns.name = name
    return ns

def iter_namespaces():
    for name in __namespace_classes__:
        yield name, for_name(name)

def default_namespace():
    return for_name(DEFAULT_NAMESPACE)

def for_name(name):
    try:
        return __namespaces__[name]
    except KeyError:
        raise LookupError(name)
