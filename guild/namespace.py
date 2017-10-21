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

from __future__ import absolute_import
from __future__ import division

import guild
import guild.model
from .entry_point_util import EntryPointResources

_namespaces = EntryPointResources("guild.namespaces", "namespace")

class Membership(object):
    yes = "yes"
    no = "no"
    maybe = "maybe"

class Namespace(object):

    # pylint: disable=no-self-use

    def __init__(self, ep):
        self.name = ep.name

    def __repr__(self):
        return "<guild.namespace.Namespace '%s'>" % self.name

    def pip_install_info(self, _req):
        """Returns info for use in the pip install command.

        Return value is a tuple of name and a list of index URLs. The
        first index URL should be used as the primary index URL and
        subsequent URLs should be used as "extra" index URLs.
        """
        raise NotImplementedError()

    def is_project_name_member(self, _project_name):
        """Returns a tuple of membership and package name for project name.

        Membership may be 'yes', 'no', or 'mabye'. Use Membership.ATTR
        to test values.

        If a namespace returns 'no', package name must be None.

        If a namespace returns 'yes' or 'maybe', package name must be
        the name of the Guild package under the namespace.
        """
        raise NotImplementedError()

class pypi(Namespace):

    INDEX_INSTALL_URL = "https://pypi.python.org/simple"

    def pip_install_info(self, req):
        return (req, [self.INDEX_INSTALL_URL])

    def is_project_name_member(self, name):
        return Membership.maybe, self.name + "/" + name

class gpkg(pypi):

    def pip_install_info(self, req):
        return ("gpkg." + req, [self.INDEX_INSTALL_URL])

    @staticmethod
    def is_project_name_member(name):
        if name.startswith("gpkg."):
            return Membership.yes, name[5:]
        else:
            return Membership.no, None

class modelfile(Namespace):

    @staticmethod
    def pip_install_info(_name):
        raise TypeError("modelfiles cannot be installed using pip")

    @staticmethod
    def is_project_name_member(name):
        if name.startswith(".modelfile."):
            parts = name[11:].split("/", 1)
            project_name = guild.model.unescape_project_name(parts[0])
            rest = "/" + parts[1] if len(parts) == 2 else ""
            return Membership.yes, project_name + rest
        else:
            return Membership.no, None

def iter_namespaces():
    return iter(_namespaces)

def for_name(name):
    return _namespaces.one_for_name(name)

def limit_to_builtin():
    _namespaces.set_path([guild.__pkgdir__])

def apply_namespace(project_name):
    ns = None
    pkg_name = None
    for _, maybe_ns in iter_namespaces():
        membership, maybe_pkg_name = (
            maybe_ns.is_project_name_member(project_name))
        if membership == Membership.yes:
            # Match, stop looking
            ns = maybe_ns
            pkg_name = maybe_pkg_name
            break
        elif membership == Membership.maybe:
            # Possible match, keep looking
            ns = maybe_ns
            pkg_name = maybe_pkg_name
    assert ns, project_name
    assert pkg_name
    return pkg_name
