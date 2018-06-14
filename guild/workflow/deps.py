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

RESOURCE_TERM = r"[a-zA-Z0-9_\-\.]+"

def dep_resdef(spec, opdef):
    return util.find_apply(
        [_model_resdef,
         _guildfile_resdef,
         _package_resdef],
        spec, opdef)

def _model_resource(spec, opdef):
    m = re.match(r"(%s)$" % RESOURCE_TERM, spec)
    if m is None:
        return None
    res_name = m.group(1)
    resdef = modeldef.get_resource(res_name)
    if resdef is None:

    return _modeldef_resource(ctx.opdef.modeldef, res_name, ctx)

def _modeldef_resource(modeldef, res_name, ctx):
    resdef = modeldef.get_resource(res_name)
    if resdef is None:
        raise DependencyError(
            "resource '%s' required by operation '%s' is not defined"
            % (res_name, ctx.opdef.fullname))
    return Resource(resdef, modeldef.guildfile.dir, ctx)

def _guildfile_resource(spec, ctx):
    m = re.match(r"(%s):(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    model_name = m.group(1)
    modeldef = ctx.opdef.guildfile.models.get(model_name)
    if modeldef is None:
        raise DependencyError(
            "model '%s' in resource '%s' required by operation "
            "'%s' is not defined"
            % (model_name, spec, ctx.opdef.fullname))
    res_name = m.group(2)
    return _modeldef_resource(modeldef, res_name, ctx)

def _packaged_resource(spec, ctx):
    m = re.match(r"(%s)/(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    pkg_name = m.group(1)
    res_name = m.group(2)
    try:
        resources = list(resource.for_name(res_name))
    except LookupError:
        pass
    else:
        for res in resources:
            if namespace.apply_namespace(res.dist.project_name) == pkg_name:
                location = os.path.join(
                    res.dist.location,
                    res.dist.key.replace(".", os.path.sep))
                return Resource(res.resdef, location, ctx)
    raise DependencyError(
        "resource '%s' required by operation '%s' is not installed"
        % (spec, ctx.opdef.fullname))
