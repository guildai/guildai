# Copyright 2017-2018 TensorHub, Inc.
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

import os
import re

from guild import namespace
from guild import resource as resourcelib
from guild import util

RESOURCE_TERM = r"[a-zA-Z0-9_\-\.]+"

class DependencyError(Exception):
    pass

def dep_resdef(spec, opdef):
    return util.find_apply(
        [_model_resdef,
         _guildfile_resdef,
         _package_resdef],
        spec, opdef)

def _model_resdef(spec, opdef):
    m = re.match(r"(%s)$" % RESOURCE_TERM, spec)
    if m is None:
        return None
    res_name = m.group(1)
    resdef = opdef.modeldef.get_resource(res_name)
    if resdef is None:
        raise RuntimeError("TODO")
    return _modeldef_resdef(opdef.modeldef, res_name, opdef)

def _modeldef_resdef(modeldef, res_name, opdef):
    resdef = modeldef.get_resource(res_name)
    if resdef is None:
        raise DependencyError(
            "resource '%s' required by operation '%s' is not defined"
            % (res_name, opdef.fullname))
    return resdef

def _guildfile_resdef(spec, opdef):
    m = re.match(r"(%s):(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    model_name = m.group(1)
    modeldef = opdef.guildfile.models.get(model_name)
    if modeldef is None:
        raise DependencyError(
            "model '%s' in resource '%s' required by operation "
            "'%s' is not defined"
            % (model_name, spec, opdef.fullname))
    res_name = m.group(2)
    return _modeldef_resdef(modeldef, res_name, opdef)

def _package_resdef(spec, opdef):
    m = re.match(r"(%s)/(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    pkg_name = m.group(1)
    res_name = m.group(2)
    try:
        resources = list(resourcelib.for_name(res_name))
    except LookupError:
        pass
    else:
        for res in resources:
            if namespace.apply_namespace(res.dist.project_name) == pkg_name:
                _location = os.path.join(
                    res.dist.location,
                    res.dist.key.replace(".", os.path.sep))
                return res.resdef
    raise DependencyError(
        "resource '%s' required by operation '%s' is not installed"
        % (spec, opdef.fullname))
