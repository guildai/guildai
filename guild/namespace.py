# Copyright 2017-2019 TensorHub, Inc.
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

from __future__ import absolute_import
from __future__ import division

import re

from collections import namedtuple

import guild
from guild.entry_point_util import EntryPointResources

_namespaces = EntryPointResources("guild.namespaces", "namespace")

DEFAULT_NAMESPACE = "pypi"

class Membership(object):
    yes = "yes"
    no = "no"
    maybe = "maybe"

PipInfo = namedtuple("PipInfo", ["project_name", "install_urls"])

class NamespaceError(LookupError):
    """Raised if a namespace doesn't exist."""

    def __init__(self, value):
        super(NamespaceError, self).__init__(value)
        self.value = value

class Namespace(object):

    # pylint: disable=no-self-use

    def __init__(self, ep):
        self.name = ep.name

    def __repr__(self):
        return "<guild.namespace.Namespace '%s'>" % self.name

    def project_name_membership(self, _project_name):
        """Returns a Membership value for a project name.

        Membership may be 'yes', 'no', or 'mabye'. Use Membership.ATTR
        to test values.

        If a namespace returns 'no' calls to `package_name` must raise
        TypeError.
        """
        raise NotImplementedError()

    def pip_info(self, _req):
        """Returns PipInfo for a package or requirement spec.
        """
        raise NotImplementedError()

    def package_name(self, _project_name):
        """Returns Guild package name for a given project name.

        Raises TypeError if project name is not a namespace member.
        """
        raise NotImplementedError()

class PypiNamespace(Namespace):

    INDEX_INSTALL_URL = "https://pypi.python.org/simple"

    def project_name_membership(self, _name):
        return Membership.maybe

    def pip_info(self, req):
        return PipInfo(req, [self.INDEX_INSTALL_URL])

    def package_name(self, project_name):
        return project_name

class PrefixNamespace(Namespace):

    prefix = None
    pip_install_urls = [PypiNamespace.INDEX_INSTALL_URL]

    def project_name_membership(self, name):
        return (Membership.yes if name.startswith(self.prefix)
                else Membership.no)

    def pip_info(self, req):
        return PipInfo(self.prefix + req, self.pip_install_urls)

    def package_name(self, project_name):
        if not project_name.startswith(self.prefix):
            raise TypeError(
                "%s is not a member of %s namespace"
                % (project_name, self.name))
        return project_name[len(self.prefix):]

def iter_namespaces():
    return iter(_namespaces)

def for_name(name):
    try:
        return _namespaces.one_for_name(name)
    except LookupError:
        raise NamespaceError(name)

def for_project_name(project_name):
    ns = None
    for _, maybe_ns in iter_namespaces():
        membership = maybe_ns.project_name_membership(project_name)
        if membership == Membership.yes:
            ns = maybe_ns
            break
        elif membership == Membership.maybe:
            ns = maybe_ns
    assert ns, project_name
    return ns

def apply_namespace(project_name):
    return for_project_name(project_name).package_name(project_name)

def split_name(name):
    """Returns a tuple of namespace and split name.
    """
    m = re.match(r"(.+?)\.(.+)", name)
    if m:
        try:
            ns = for_name(m.group(1))
        except NamespaceError:
            pass
        else:
            if ns.name != DEFAULT_NAMESPACE:
                return ns, m.group(2)
    return for_name(DEFAULT_NAMESPACE), name

def limit_to_builtin():
    _namespaces.set_path([guild.__pkgdir__])

def pip_info(pkg):
    ns, req = split_name(pkg)
    return ns.pip_info(req)
