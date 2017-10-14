# Copyright 2017 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import enum
import importlib

__namespace_classes__ = {
    "gpkg": "guild.namespace.gpkg",
    "pypi": "guild.namespace.pypi",
}

__namespaces__ = {}

class NamespaceError(LookupError):
    """Raised if a namespace doesn't exist."""

    def __init__(self, value):
        super(NamespaceError, self).__init__(value)
        self.value = value

Membership = enum.Enum("guild.namespace.Membership", "yes no maybe")

class Namespace(object):

    name = None

    def pip_install_info(_self, _req):
        """Returns info for use in the pip install command.

        Return value is a tuple of name and a list of index URLs. The
        first index URL should be used as the primary index URL and
        subsequent URLs should be used as "extra" index URLs.
        """
        raise NotImplementedException()

    def is_member(_self, _project_name):
        """Returns a tuple of membership and package name for project name.

        Membership may be yes, no, or mabye.

        If a namespace returns no, package name must be None.

        If a namespace returns yes or maybe, package name must be the
        package name under the namespace.
        """
        raise NotImplementedException()


class pypi(Namespace):

    INDEX_INSTALL_URL = "https://pypi.python.org/simple"

    def pip_install_info(self, req):
        return (req, [self.INDEX_INSTALL_URL])

    @staticmethod
    def is_member(name):
        return Membership.maybe, name

class gpkg(pypi):

    def pip_install_info(self, req):
        return ("gpkg." + req, [self.INDEX_INSTALL_URL])

    @staticmethod
    def is_member(name):
        if name.startswith("gpkg."):
            return Membership.yes, name[5:]
        else:
            return Membership.no, None

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

def for_name(name):
    try:
        return __namespaces__[name]
    except KeyError:
        raise NamespaceError(name)
