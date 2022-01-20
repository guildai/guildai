# Copyright 2017-2022 TensorHub, Inc.
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

"""TODO:

- Expose 'pipeline' switch as flag to a DvC operation
- Link to upstream stages from pipeline op
- Support for flags
  - Pipeline level (all available params from dvc.param)
  - Stage level (stage specific params from dvc.param)

Flags I think will require in-place editing of the params file for the
run. To preserve the copy of params that was used, this file must be
copied to the run dir immediately after changing it and before
starting the op.

What to do with inputs to an operation? Should these be copied into
the run directory as well, but before the operation starts? How else
can you track these files? Maybe there's a flag to the stage op to
configure this behavior.

Maybe these options:

- Copy inputs
- Don't copy inputs
- Link to cached inputs

XXX - before biting down on the "run in project dir + copy", play
around with "copy + run in run dir" using the same basic logic. Always
copying from the project and maintaining shared cache/tmp dirs. I
think the problem here will be, what to copy. Not sure!

I think the risk to the above is:

- It gets complicated, with Guild knowing a lot about everything that
  DvC does
- With the complexity, it'll be hard for users to know what's going on
- Is there a need for this, given that DvC works that way

Counterpoint:

- It's a much better model, to copy the repo and run from the run dir
- If we can find a simple Zen implementation, it might not be
  complicated

"""

from __future__ import absolute_import
from __future__ import division

import logging
import os

import yaml

import guild

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import util

log = logging.getLogger("guild")


class _DvcModelProxy(object):

    name = "dvc.yaml"

    def __init__(self, target_stage, config_dir):
        self.modeldef = _init_dvc_modeldef(self.name, target_stage, config_dir)
        self.reference = _init_dvc_model_reference()


def _init_dvc_modeldef(model_name, target_stage, config_dir):
    data = [
        {
            "model": model_name,
            "operations": {
                target_stage: {
                    "exec": (
                        "${python_exe} -um guild.plugins.dvc_stage_main "
                        "--project-dir %s %s"
                        % (util.shlex_quote(config_dir), util.shlex_quote(target_stage))
                    ),
                }
            },
        }
    ]
    gf = guildfile.Guildfile(data, src="<guild.plugins._DvcModelProxy>")
    return gf.models[model_name]


def _init_dvc_model_reference():
    return modellib.ModelRef("builtin", "guildai", guild.__version__, "dvc.yaml")


class _Stage:
    def __init__(self, name, config, config_dir):
        self.name = name
        self.config = config
        self.config_dir = config_dir


class DvcPlugin(pluginlib.Plugin):
    @staticmethod
    def guildfile_loaded(gf):
        for m in gf.models.values():
            _maybe_apply_dvc_stages(m.extra, m)

    @staticmethod
    def resolve_model_op(opspec):
        if opspec.startswith("dvc.yaml:"):
            target_stage = opspec[9:]
            model = _DvcModelProxy(target_stage, os.path.abspath(config.cwd()))
            return model, target_stage
        return None


def _maybe_apply_dvc_stages(model_config, model):
    for stage in _iter_dvc_stages(model_config, _model_dir(model)):
        _add_or_merge_operation_for_stage(stage, model)


def _model_dir(model):
    return model.guildfile.dir


def _iter_dvc_stages(dvc_config, config_dir):
    stages_import = _coerce_dvc_stages_import(dvc_config.get("dvc-stages-import"))
    if not stages_import:
        return
    dvc_config = _load_dvc_config_for_stages_import(config_dir)
    for stage_name, stage_config in (dvc_config.get("stages") or {}).items():
        if _filter_dvc_stage(stage_name, stages_import):
            yield _Stage(stage_name, stage_config, config_dir)


def _coerce_dvc_stages_import(val):
    if val is None or isinstance(val, (list, bool)) or val == "all":
        return val
    if isinstance(val, str):
        return [val]
    log.warning(
        "invalid value for 'dvc-stages-import' %r - "
        "expected boolean, 'all', or list of stage names",
        val,
    )
    return None


def _load_dvc_config_for_stages_import(dir):
    config_filename = _dvc_config_filename(dir)
    if not os.path.exists(config_filename):
        log.warning(
            "%s not found - skipping DvC stages import",
            os.path.relpath(config_filename),
        )
        return {}
    log.debug("loading %s for DvC stages import", config_filename)
    with open(config_filename) as f:
        return yaml.safe_load(f)


def _dvc_config_filename(dir):
    return os.path.join(dir, "dvc.yaml")


def _filter_dvc_stage(name, import_spec):
    if import_spec in (True, "all"):
        return True
    if isinstance(import_spec, list) and name in import_spec:
        return True
    return False


def _add_or_merge_operation_for_stage(stage, model):
    opdef = _ensure_opdef(stage.name, model)
    log.debug("importing DvC stage '%s' as '%s'", stage.name, opdef.fullname)
    _apply_stage_config_to_opdef(stage, opdef)


def _ensure_opdef(name, model):
    opdef = model.get_operation(name)
    if not opdef:
        opdef = _init_opdef(name, model)
        model.operations.append(opdef)
    return opdef


def _init_opdef(name, model):
    return guildfile.OpDef(name, {}, model)


def _apply_stage_config_to_opdef(stage, opdef):
    if opdef.main:
        log.warning(
            "ignoring operation main attribute %r for DvC stage import", opdef.main
        )
    opdef.main = "guild.plugins.dvc_stage_main --pipeline --project-dir %s %s" % (
        util.shlex_quote(stage.config_dir),
        util.shlex_quote(stage.name),
    )
