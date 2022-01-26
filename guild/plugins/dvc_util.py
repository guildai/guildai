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

from __future__ import absolute_import
from __future__ import division

import logging
import os

import yaml

from guild import util
from guild import var

log = logging.getLogger("guild")


def load_dvc_config(dir):
    yaml_filename = dvc_yaml_path(dir)
    if not os.path.exists(yaml_filename):
        log.warning(
            "%s not found - skipping DvC stages import",
            os.path.relpath(yaml_filename),
        )
        return {}
    log.debug("loading %s for DvC stages import", yaml_filename)
    with open(yaml_filename) as f:
        return yaml.safe_load(f)


def dvc_yaml_path(dir):
    return os.path.join(dir, "dvc.yaml")


def iter_stage_deps(stage, dvc_config):
    out_stages_lookup = None  # lazy init of stages lookup
    stage_config = _stage_config(stage, dvc_config)
    for dep in _stage_deps(stage_config):
        out_stages_lookup = _ensure_out_stages_lookup(out_stages_lookup, dvc_config)
        yield dep, out_stages_lookup.get(dep)


def _ensure_out_stages_lookup(out_stages, dvc_config):
    if out_stages is not None:
        return out_stages
    return _out_stages(dvc_config)


def _out_stages(dvc_config):
    out_stages = {}
    for stage_name, stage_config in _stages_config(dvc_config).items():
        for out in _stage_outs(stage_config):
            out_stages[out] = stage_name
    return out_stages


def _stages_config(dvc_config):
    return dvc_config.get("stages", {})


def _stage_config(stage, dvc_config):
    try:
        return _stages_config(dvc_config)[stage]
    except KeyError:
        raise ValueError("no such stage: %s" % stage)


def _stage_outs(stage_config):
    return stage_config.get("outs", [])


def _stage_deps(stage_config):
    return stage_config.get("deps", [])


def iter_stage_params(stage, dvc_config):
    stage_config = _stage_config(stage, dvc_config)
    for item in _stage_params(stage_config):
        if isinstance(item, str):
            yield item, "params.yaml"
        elif isinstance(item, dict):
            for key, val in item.items():
                yield val, key
        else:
            assert False, item


def _stage_params(stage_config):
    return stage_config.get("params", [])


def marked_or_latest_run_for_stage(dvc_config_path, stage):
    runs = runs_for_stage(dvc_config_path, stage)
    if not runs:
        return None
    for run in runs:
        if run.get("marked"):
            return run
    return runs[0]


def runs_for_stage(dvc_config_path, stage):
    return var.runs(
        sort=["-started"],
        filter=_dvc_stage_op_filter(dvc_config_path, stage),
    )


def _dvc_stage_op_filter(dvc_config_path, stage):
    dvc_config_path = _ensure_config_dir(dvc_config_path)

    def f(run):
        opref = run.opref
        return (
            opref.op_name == stage
            and opref.pkg_type in ("guildfile", "import")
            and _match_dvc_path(opref.pkg_name, dvc_config_path)
            and run.status == "completed"
        )

    return f


def _ensure_config_dir(dvc_config_path):
    if dvc_config_path.endswith("dvc.yaml"):
        return os.path.dirname(dvc_config_path)
    return dvc_config_path


def _match_dvc_path(opref_pkg_name, target_path):
    opref_path = os.path.dirname(opref_pkg_name)
    return util.compare_paths(opref_path, target_path)
