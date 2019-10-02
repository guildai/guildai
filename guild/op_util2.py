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

import os

from guild import config
from guild import guildfile
from guild import file_util
from guild import run as runlib
from guild import util
from guild import var

# TEMP imports until promoted to op_util
from .op_util import NO_ARG_VALUE           # pylint: disable=unused-import
from .op_util import ArgValueError          # pylint: disable=unused-import
from .op_util import mapped_flag_vals       # pylint: disable=unused-import
from .op_util import parse_flag_assigns     # pylint: disable=unused-import
from .op_util import parse_opspec           # pylint: disable=unused-import
from .op_util import split_cmd              # pylint: disable=unused-import

###################################################################
# Error classes
###################################################################

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

###################################################################
# Resolve opspec
###################################################################

def opdef_for_opspec(opspec):
    model, op_name = _model_op(opspec)
    opdef = _opdef_for_model_op(model, op_name)
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

def _opdef_for_model_op(model, op_name):
    if op_name:
        return model.modeldef.get_operation(op_name)
    return model.modeldef.default_operation

###################################################################
# Run support
###################################################################

def init_run(path=None):
    if not path:
        run_id = runlib.mkid()
        path = os.path.join(var.runs_dir(), run_id)
    else:
        run_id = os.path.basename(path)
    return runlib.Run(run_id, path)

def set_run_pending(run):
    open(run.guild_path("PENDING"), "w").close()

def write_sourcecode_digest(run):
    digest = file_util.files_digest(run.guild_path("sourcecode"))
    run.write_attr("sourcecode_digest", digest)

###################################################################
# Utils
###################################################################

def split_batch_files(flag_args):
    batch_files = []
    rest = []
    for arg in flag_args:
        if arg[:1] == "@":
            batch_files.append(arg[1:])
        else:
            rest.append(arg)
    return batch_files, rest
