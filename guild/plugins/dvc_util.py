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

import json
import logging
import os
import subprocess

import yaml

from guild import util
from guild import var

log = logging.getLogger("guild")


class DvcInitError(Exception):
    pass


class DvcPullError(Exception):
    pass


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
    """Returns an iteration of dep, parent_stage tuples for a stage.

    If a dependency doesn't have a parent (i.e. it relies on a local
    file) the parent stage in the tuple is None.
    """
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
    except KeyError as e:
        raise ValueError(f"no such stage: {stage}") from e


def _stage_outs(stage_config):
    return stage_config.get("outs", [])


def _stage_deps(stage_config):
    return stage_config.get("deps", [])


def iter_stage_deps_by_parent(stage, dvc_config):
    deps = {}
    for dep, parent_stage in iter_stage_deps(stage, dvc_config):
        deps.setdefault(parent_stage, []).append(dep)
    for parent_stage in sorted(deps, key=lambda x: x if x is not None else ""):
        yield parent_stage, deps[parent_stage]


def iter_stage_params(stage, dvc_config):
    """Returns an iteration of param_name and filename containing param."""
    stage_config = _stage_config(stage, dvc_config)
    for item in _stage_params(stage_config):
        if isinstance(item, str):
            yield item, "params.yaml"
        elif isinstance(item, dict):
            for key, val in item.items():
                if isinstance(val, str):
                    yield val, key
                elif isinstance(val, list):
                    for val_item in val:
                        yield val_item, key
                else:
                    assert False, (val, item)
        else:
            assert False, item


def _stage_params(stage_config):
    return stage_config.get("params", [])


def marked_or_latest_run_for_stage(stage, run_id_prefix=None, status=None):
    status = status or ("completed",)
    runs = runs_for_stage(stage, run_id_prefix, status)
    if not runs:
        return None
    for run in runs:
        if run.get("marked"):
            return run
    return runs[0]


def runs_for_stage(stage, run_id_prefix=None, status=None):
    return var.runs(
        sort=["-started"],
        filter=_dvc_stage_op_filter(stage, run_id_prefix, status),
    )


def _dvc_stage_op_filter(stage, run_id_prefix, status):
    assert stage
    assert status

    # If full run ID specified, select matching run regardless of
    # stage and status.
    if run_id_prefix and len(run_id_prefix) == 32:
        return lambda run: run.id == run_id_prefix

    def f(run):
        return (
            _filter_run_id(run, run_id_prefix)
            and _filter_run_dvc_stage(run, stage)
            and _filter_run_status(run, status)
        )

    return f


def _filter_run_id(run, run_id_prefix):
    return not run_id_prefix or run.id.startswith(run_id_prefix)


def _filter_run_dvc_stage(run, stage):
    return run.get("dvc-stage") == stage


def _filter_run_status(run, status):
    return run.status in status


def ensure_dvc_repo(run_dir, project_dir):
    _ensure_git_repo(run_dir)
    _ensure_dvc_config(run_dir, project_dir)
    _ensure_shared_dvc_cache(run_dir, project_dir)


def _ensure_git_repo(run_dir):
    try:
        _ignored = subprocess.check_output(["git", "init"], cwd=run_dir)
    except FileNotFoundError as e:
        raise DvcInitError(
            f"cannot initialize Git in run directory {run_dir} "
            "(required for 'dvc pull') - is Git installed and "
            "available on the path?"
        ) from e
    except subprocess.CalledProcessError as e:
        raise DvcInitError(
            f"error initializing Git repo in run directory {run_dir} "
            "(required for 'dvc pull')"
        ) from e


def _ensure_dvc_config(run_dir, project_dir):
    if os.path.exists(os.path.join(run_dir, ".dvc", "config")):
        return
    util.find_apply(
        [
            _try_copy_dvc_config,
            _try_copy_dvc_config_in,
            _no_dvc_config_resolution_error,
        ],
        project_dir,
        run_dir,
    )


def _try_copy_dvc_config(project_dir, run_dir):
    src = os.path.join(project_dir, ".dvc", "config")
    if not os.path.exists(src):
        return None
    dest = os.path.join(run_dir, ".dvc", "config")
    util.ensure_dir(os.path.dirname(dest))
    util.copyfile(src, dest)
    return dest


def _try_copy_dvc_config_in(project_dir, run_dir):
    src = os.path.join(project_dir, "dvc.config.in")
    if not os.path.exists(src):
        return None
    dest = os.path.join(run_dir, ".dvc", "config")
    util.ensure_dir(os.path.dirname(dest))
    util.copyfile(src, dest)
    return dest


def _no_dvc_config_resolution_error(project_dir, _run_dir):
    raise DvcInitError(
        "cannot find DvC config ('.dvc/config' or 'dvc.config.in') "
        f"in {os.path.relpath(project_dir)} (required for 'dvc pull')"
    )


def _ensure_shared_dvc_cache(run_dir, project_dir):
    dest = os.path.join(run_dir, ".dvc", "cache")
    if os.path.exists(dest):
        return
    src = os.path.join(project_dir, ".dvc", "cache")
    if not os.path.exists(src):
        return
    util.symlink(src, dest)


def pull_dvc_dep(dep, run_dir, project_dir, remote=None):
    _ensure_dvc_file(dep, run_dir, project_dir)
    return _pull_dep(dep, run_dir, remote)


def _ensure_dvc_file(dep, run_dir, project_dir):
    dvc_file_name = dep + ".dvc"
    dest = os.path.join(run_dir, dvc_file_name)
    if os.path.exists(dest):
        return
    src = os.path.join(project_dir, dvc_file_name)
    if not os.path.exists(src):
        raise DvcPullError(
            f"cannot find DvC file {dvc_file_name} in "
            f"{os.path.relpath(project_dir)} (required for 'dvc pull')"
        )
    util.ensure_dir(os.path.dirname(dest))
    util.copyfile(src, dest)


def _pull_dep(dep, run_dir, remote=None):
    cmd = ["dvc", "pull", dep]
    if remote:
        cmd.extend(["--remote", remote])
    log.info("Fetching DvC resource %s", dep)
    log.debug("dvc pull cmd: %s", cmd)
    try:
        subprocess.check_call(["dvc", "pull", dep], cwd=run_dir)
    except subprocess.CalledProcessError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("cmd: %s", cmd)
        raise DvcPullError(
            f"error fetching DvC resource {dep}: 'dvc pull' exited with "
            f"non-zero exit status {e.returncode} (see above for details)"
        ) from e
    else:
        dep_path = os.path.join(run_dir, dep)
        if not os.path.exists(dep_path):
            raise DvcPullError(
                f"'dvc pull' did not fetch the expected file {dep} "
                "(see above for details)"
            )
        return dep_path


def iter_stage_metrics_data(stage, run_dir):
    dvc_config = load_dvc_config(run_dir)
    for name in _iter_stage_metrics_names(stage, dvc_config):
        data = _load_metrics(os.path.join(run_dir, name))
        yield name, data


def _iter_stage_metrics_names(stage, dvc_config):
    stage_metrics = _stage_metrics(_stage_config(stage, dvc_config))
    for x in stage_metrics:
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for name in x:
                yield name
        else:
            log.warning(
                "unexpected metrics value %r for stage '%s', skipping",
                x,
                stage,
            )


def _stage_metrics(stage_config):
    return stage_config.get("metrics", [])


def _load_metrics(path):
    ext = os.path.splitext(path)[1]
    if ext in (".yml", "yaml"):
        return _load_yaml(path)
    if ext in (".json",):
        return _load_json(path)
    raise ValueError(f"unsupported metrics type in {path}")


def _load_yaml(path):
    return yaml.safe_load(open(path))


def _load_json(path):
    return json.load(open(path))
