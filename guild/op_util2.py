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

from guild import config
from guild import guildfile
from guild import util

# TEMP imports until promoted to op_util
from .op_util import parse_opspec

class InvalidOpSpec(Exception):

    def __init__(self, opspec):
        super(InvalidOpSpec, self).__init__(opspec)
        self.opspec = opspec

class NoSuchModel(Exception):

    def __init__(self, opspec):
        super(NoSuchModel, self).__init__(opspec)
        self.opspec = opspec

class NoSuchOperation(Exception):

    def __init__(self, model, op_name):
        super(NoSuchOperation, self).__init__(model, op_name)
        self.model = model
        self.op_name = op_name

class CwdGuildfileError(Exception):

    def __init__(self, guildfile_error):
        super(CwdGuildfileError, self).__init__(guildfile_error)
        self.msg = guildfile_error.msg
        self.path = guildfile_error.path

class MultipleMatchingModels(Exception):

    def __init__(self, model_ref, matches):
        super(MultipleMatchingModels, self).__init__(model_ref, matches)
        self.model_ref = model_ref
        self.matches = matches

class NoMatchingModel(Exception):

    def __init__(self, model_ref):
        super(NoMatchingModel, self).__init__(model_ref)
        self.model_ref = model_ref

def opdef_for_opspec(opspec):
    model, op_name = _model_op(opspec)
    opdef = model.modeldef.get_operation(op_name)
    if not opdef:
        raise NoSuchOperation(model, op_name)
    return opdef

def _model_op(opspec):
    model_ref, op_name = _parse_opspec(opspec)
    model = _resolve_model(model_ref)
    if not model:
        raise NoSuchModel(opspec)
    return model, op_name

def _parse_opspec(opspec):
    parsed = parse_opspec(opspec)
    if parsed is None:
        raise InvalidOpSpec(opspec)
    return parsed

def _resolve_model(model_ref):
    return util.find_apply([
        _resolve_cwd_model,
        _resolve_system_model,
    ], model_ref)

def _resolve_cwd_model(model_ref):
    from guild import model as modellib # expensive
    cwd_guildfile = _cwd_guildfile()
    if not cwd_guildfile:
        return None
    with modellib.SetPath([cwd_guildfile.dir], clear_cache=True):
        return _match_one_model(model_ref, cwd_guildfile)

def _cwd_guildfile():
    """Returns a Guild file object in cwd if a Guild file exists there.

    Returns None if a Guild file is not defined in the cwd.

    Raises CwdGuildfileError if a Guild file exists but is not valid.
    """
    try:
        return guildfile.from_dir(config.cwd())
    except guildfile.GuildfileError as e:
        raise CwdGuildfileError(e)

def _resolve_system_model(model_ref):
    return _match_one_model(model_ref)

def _match_one_model(model_ref, cwd_guildfile=None):
    matches = list(_iter_matching_models(model_ref, cwd_guildfile))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 0 and model_ref:
        return _complete_match_one_model(model_ref, matches)
    return None

def _iter_matching_models(model_ref, cwd_guildfile):
    from guild import model as modellib # expensive
    for model in modellib.iter_models():
        if model_ref:
            if _match_model_ref(model_ref, model):
                yield model
        else:
            if cwd_guildfile and _is_default_cwd_model(model, cwd_guildfile):
                yield model
                break
            if not model.name:
                yield model

def _is_default_cwd_model(model, cwd_guildfile):
    default_model = cwd_guildfile.default_model
    return (default_model and
            default_model.guildfile.dir == model.modeldef.guildfile.dir and
            default_model.name == model.name)

def _match_model_ref(model_ref, model):
    if "/" in model_ref:
        return model_ref in model.fullname
    else:
        return model_ref in model.name

def _complete_match_one_model(model_ref, matches):
    complete_match = _model_by_name(model_ref, matches)
    if complete_match:
        return complete_match
    raise MultipleMatchingModels(model_ref, matches)

def _model_by_name(name, models):
    for model in models:
        if model.name == name:
            return model
    return None

def _maybe_no_model_error(model_ref):
    if model_ref:
        raise NoMatchingModel(model_ref)
    return None
