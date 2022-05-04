# Copyright 2017-2022 RStudio, PBC
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

- Complete stage import (should function like dvc example prototypes)
- Do we care about pipelines vs not?
- Cleanup / lint (remove unused or commented out code)
"""

import copy
import logging
import os
from typing import Optional

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import resolver as resolverlib
from guild import resourcedef
from guild import util

from . import dvc_util

log = logging.getLogger("guild")


class _DvcModelProxy(object):

    name = "dvc.yaml"

    def __init__(self, target_stage, project_dir):
        self.modeldef = _init_dvc_modeldef(self.name, target_stage, project_dir)
        self.reference = _init_dvc_model_reference(project_dir)


def _init_dvc_modeldef(model_name, stage_name, project_dir):
    data = [
        {
            "model": model_name,
            "operations": {
                stage_name: _stage_op_data(stage_name, project_dir),
            },
        }
    ]
    log.debug("data for DvC stage '%s':\n%s", stage_name, _lazy_pformat(data))
    gf = guildfile.Guildfile(
        data,
        src="<guild.plugins._DvcModelProxy>",
        dir=project_dir,
    )
    _apply_config_flags(gf, model_name, stage_name)
    return gf.models[model_name]


def _lazy_pformat(x):
    from guild import yaml_util

    return yaml_util.encode_yaml(x)


def _stage_op_data(stage_name, project_dir):
    dvc_config = dvc_util.load_dvc_config(project_dir)
    op_data = {
        "main": "guild.plugins.dvc_stage_main --project-dir %s %s"
        % (
            util.shlex_quote(project_dir),
            util.shlex_quote(stage_name),
        ),
        "description": "Stage '%s' imported from dvc.yaml" % stage_name,
    }
    _apply_stage_flags_data(stage_name, dvc_config, op_data)
    _apply_stage_deps_data(stage_name, dvc_config, op_data)
    return op_data


def _apply_stage_flags_data(stage, dvc_config, data):
    applied_flags_dest = None
    imports = set()
    for param_name, config_name in dvc_util.iter_stage_params(stage, dvc_config):
        if applied_flags_dest is None:
            data["flags-dest"] = "config:%s" % config_name
            imports.add(param_name)
            applied_flags_dest = config_name
        elif applied_flags_dest != config_name:
            log.warning(
                "DvC stage '%s' uses multiple param files, ignoring "
                "subsequent file %s for flags import",
                stage,
                config_name,
            )
        else:
            imports.add(param_name)
    data["flags-import"] = sorted(imports)


def _apply_stage_deps_data(stage, dvc_config, opdef_data):
    requires_data = opdef_data.setdefault("requires", [])
    if not isinstance(requires_data, list):
        log.warning(
            "unexpected value for 'requires' - expected a list, " "skipping DvC deps"
        )
        return
    for parent_stage, deps in dvc_util.iter_stage_deps_by_parent(stage, dvc_config):
        _apply_stage_dep_data(parent_stage, deps, requires_data)


def _apply_stage_dep_data(parent_stage, deps, requires_data):
    if parent_stage is not None:
        _apply_operation_dep(parent_stage, deps, requires_data)
    else:
        _apply_dvcfile_deps(deps, requires_data)


def _apply_operation_dep(parent_stage, deps, requires_data):
    requires_data.append(
        {
            "dvcstage": parent_stage,
            "select": deps,
        }
    )


def _apply_dvcfile_deps(deps, requires_data):
    requires_data.extend([{"dvcfile": dep} for dep in deps])


def _apply_config_flags(gf, model_name, op_name):
    from . import config_flags

    stage_opdef = gf.models[model_name].get_operation(op_name)
    config_flags.apply_config_flags(stage_opdef)


def _init_dvc_model_reference(project_dir):
    dvc_yaml_path = os.path.join(project_dir, "dvc.yaml")
    if os.path.isfile(dvc_yaml_path):
        version = modellib.file_hash(dvc_yaml_path)
    else:
        version = "unknown"
    return modellib.ModelRef("import", dvc_yaml_path, version, "dvc.yaml")


class _Stage:
    def __init__(self, name, config, project_dir):
        self.name = name
        self.config = config
        self.project_dir = project_dir


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

    @staticmethod
    def resource_source_for_data(data, resdef):
        if "dvcfile" in data:
            return _dvcfile_source(data, resdef)
        elif "dvcstage" in data:
            return _dvcstage_source(data, resdef)
        else:
            return None

    @staticmethod
    def resolver_class_for_source(source):
        if source.parsed_uri.scheme == "dvcfile":
            return _DvcFileResolver
        elif source.parsed_uri.scheme == "dvcstage":
            return _DvcStageResolver
        else:
            return None


class DvcResourceSource(resourcedef.ResourceSource):
    always_pull: bool = False
    remote: Optional[str]

    def __init__(self, resdef, uri, always_pull=False, remote="", **kw):
        super().__init__(resdef, uri, **kw)
        self.always_pull = always_pull
        self.remote = remote


def _dvcfile_source(data, resdef):
    data_copy = copy.copy(data)
    dep_spec = data_copy.pop("dvcfile")
    if not dep_spec:
        raise resourcedef.ResourceFormatError(
            "missing spec for 'dvcfile' source attribute"
        )
    always_pull = data_copy.pop("always-pull", False)
    remote = data_copy.pop("remote", None)
    source = DvcResourceSource(resdef, "dvcfile:%s" % dep_spec, **data_copy)
    source.always_pull = always_pull
    source.remote = remote
    return source


def _dvcstage_source(data, resdef):
    data_copy = copy.copy(data)
    dep_spec = data_copy.pop("dvcstage")
    if not dep_spec:
        raise resourcedef.ResourceFormatError(
            "missing spec for 'dvcstage' source attribute"
        )
    source = resourcedef.ResourceSource(resdef, "dvcstage:%s" % dep_spec, **data_copy)
    return source


class _DvcFileResolver(resolverlib.FileResolver):
    def resolve(self, resolve_context):
        return util.find_apply(
            [
                self._maybe_always_pull,
                self._try_default_resolve,
                self._pull_dep,
            ],
            resolve_context,
        )

    def _maybe_always_pull(self, resolve_context):
        if self.source.always_pull:
            return self._pull_dep(resolve_context)
        return None

    def _try_default_resolve(self, resolve_context):
        try:
            return super(_DvcFileResolver, self).resolve(resolve_context)
        except resolverlib.ResolutionError as e:
            log.debug("error trying default file resolution: %s", e)
            return None

    def _pull_dep(self, resolve_context):
        dep = self.source.parsed_uri.path
        run_dir = resolve_context.run.dir
        project_dir = self.resource.location
        _ensure_dvc_repo(run_dir, project_dir)
        remote = self.source.remote
        pulled_dep_path = _pull_dvc_dep(dep, run_dir, project_dir, remote=remote)
        return [pulled_dep_path]


def _ensure_dvc_repo(run_dir, project_dir):
    try:
        dvc_util.ensure_dvc_repo(run_dir, project_dir)
    except dvc_util.DvcInitError as e:
        raise resolverlib.ResolutionError(str(e))


def _pull_dvc_dep(dep, run_dir, project_dir, remote=None):
    try:
        return dvc_util.pull_dvc_dep(dep, run_dir, project_dir, remote=remote)
    except dvc_util.DvcPullError as e:
        raise resolverlib.ResolutionError(str(e))


class _DvcStageResolver(resolverlib.OperationResolver):
    def resolve_op_run(self, run_id_prefix=None, include_staged=False):
        stage = self.source.parsed_uri.path
        status = ("completed", "staged") if include_staged else ("completed",)
        run = dvc_util.marked_or_latest_run_for_stage(stage, run_id_prefix, status)
        if not run:
            raise resolverlib.ResolutionError("no suitable run for '%s' stage" % stage)
        return run


def _maybe_apply_dvc_stages(model_config, model):
    for stage in _iter_dvc_stages(model_config, _model_dir(model)):
        _add_or_merge_operation_for_stage(stage, model)


def _model_dir(model):
    return model.guildfile.dir


def _iter_dvc_stages(dvc_config, project_dir):
    stages_import = _coerce_dvc_stages_import(dvc_config.get("dvc-stages-import"))
    if not stages_import:
        return
    dvc_config = dvc_util.load_dvc_config(project_dir)
    for stage_name, stage_config in (dvc_config.get("stages") or {}).items():
        if _filter_dvc_stage(stage_name, stages_import):
            yield _Stage(stage_name, stage_config, project_dir)


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


def _filter_dvc_stage(name, import_spec):
    if import_spec in (True, "all"):
        return True
    if isinstance(import_spec, list) and name in import_spec:
        return True
    return False


def _add_or_merge_operation_for_stage(stage, model):
    opdef = _ensure_stage_opdef(stage, model)
    log.debug("importing DvC stage '%s' as '%s'", stage.name, opdef.fullname)


def _ensure_stage_opdef(stage, model):
    model_opdef = model.get_operation(stage.name)
    stage_opdef = _init_stage_opdef(stage, model)
    if model_opdef:
        _apply_stage_opdef_config(stage_opdef, model_opdef)
        return model_opdef
    else:
        model.operations.append(stage_opdef)
        return stage_opdef


def _init_stage_opdef(stage, model):
    return guildfile.OpDef(
        stage.name,
        _stage_op_data(stage.name, stage.project_dir),
        model,
    )


def _apply_stage_opdef_config(stage_opdef, model_opdef):
    if model_opdef.main:
        log.warning(
            "ignoring operation main attribute %r for DvC stage import",
            model_opdef.main,
        )
    model_opdef.main = stage_opdef.main
    if not model_opdef.description:
        model_opdef.description = stage_opdef.description
    if model_opdef.flags:
        log.warning("ignoring operation flags for DvC stage import")
    model_opdef.flags = list(stage_opdef.flags)
