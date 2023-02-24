# Copyright 2017-2023 Posit Software, PBC
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

import argparse

import logging
import os
import subprocess

import yaml

from guild import op_util

from guild import run as runlib

from guild import run_manifest
from guild import summary
from guild import util

from . import dvc_util

log = None


class State:
    def __init__(self, target_stage, project_dir):
        _assert_dvc_yaml(project_dir)
        self.target_stage = target_stage
        self.project_dir = project_dir
        self.run_dir = _required_run_dir()
        self.run = runlib.for_dir(self.run_dir)
        self.ran_stages = []
        self.dvc_config = _load_dvc_yaml(project_dir)
        self.parent_run = op_util.current_run()
        self.manifest_entries = []
        self.source_uri = f"dvcstage:{self.target_stage}"


def _assert_dvc_yaml(project_dir):
    dvc_yaml = os.path.join(project_dir, "dvc.yaml")
    if not os.path.exists(dvc_yaml):
        _missing_dvc_yaml_error(project_dir)


def _required_run_dir():
    run_dir = os.getenv("RUN_DIR")
    if not run_dir:
        raise SystemExit("missing required environment RUN_DIR for operation")
    return run_dir


def _load_dvc_yaml(dir):
    with open(os.path.join(dir, "dvc.yaml")) as f:
        return yaml.safe_load(f)


def main():
    op_util.init_logging()
    globals()["log"] = logging.getLogger("guild")
    args = _init_args()
    state = State(args.stage, args.project_dir)
    _handle_stage(state)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--project-dir")
    p.add_argument("stage")
    args = p.parse_args()
    _ensure_project_dir_arg(args)
    return args


def _ensure_project_dir_arg(args):
    if not args.project_dir:
        project_dir_env = os.getenv("PROJECT_DIR")
        if not project_dir_env:
            raise SystemExit(
                "unspecified project dir - specify either --project-dir "
                "or set the PROJECT_DIR environment variable"
            )
        args.project_dir = project_dir_env


def _missing_dvc_yaml_error(project_dir):
    raise SystemExit(f"invalid DvC config directory '{project_dir}' - missing dvc.yaml")


def _handle_stage(state):
    _init_run_dir(state)
    _repro_run(state)
    _log_metrics_as_summaries(state)
    _update_run_manifest(state)


def _init_run_dir(state):
    log.info("Initializing run")
    _write_run_attrs(state)
    _init_dvc_repo(state)
    _copy_dvc_yaml(state)
    _resolve_deps(state)
    _copy_params_with_flags(state)


def _write_run_attrs(state):
    state.run.write_attr("dvc-stage", state.target_stage)


def _init_dvc_repo(state):
    repo_paths = []
    try:
        dvc_util.ensure_dvc_repo(state.run_dir, state.project_dir, repo_paths)
    except dvc_util.DvcInitError as e:
        raise SystemExit(str(e)) from e
    else:
        state.manifest_entries.extend(
            _internal_file_entries_for_repo_paths(repo_paths, state)
        )


def _internal_file_entries_for_repo_paths(repo_paths, state):
    return [_internal_file_entry_for_path(path, state) for path in repo_paths]


def _internal_file_entry_for_path(path, state):
    return run_manifest.internal_file_args(
        state.run_dir,
        os.path.relpath(path, state.run_dir),
        state.source_uri,
    )


def _copy_dvc_yaml(state):
    dest = os.path.join(state.run_dir, "dvc.yaml")
    if os.path.exists(dest):
        return
    src = os.path.join(state.project_dir, "dvc.yaml")
    if not os.path.exists(src):
        raise SystemExit("missing dvc.yaml - cannot run DvC stage")
    util.copyfile(src, dest)
    state.manifest_entries.append(_internal_file_entry_for_path(dest, state))


def _resolve_deps(state):
    for dep_stage, deps in dvc_util.iter_stage_deps_by_parent(
        state.target_stage, state.dvc_config
    ):
        deps = _filter_unresolved_deps(deps, state)
        if not deps:
            continue
        if dep_stage:
            _resolve_stage_deps(dep_stage, deps, state)
        else:
            _resolve_project_deps(deps, state)


def _filter_unresolved_deps(deps, state):
    return [dep for dep in deps if not os.path.exists(os.path.join(state.run_dir, dep))]


def _resolve_stage_deps(stage, deps, state):
    stage_run = dvc_util.marked_or_latest_run_for_stage(stage)
    if not stage_run:
        _no_suitable_run_for_stage_error(stage, deps)
    log.info("Using %s for '%s' DvC stage dependency", stage_run.id, stage)
    _link_op_deps(stage_run, deps, state)


def _no_suitable_run_for_stage_error(stage, deps):
    deps_desc = ", ".join(sorted(deps))
    raise SystemExit(f"no suitable run for stage '{stage}' (needed for {deps_desc})")


def _link_op_deps(run, deps, state):
    for dep in deps:
        target = os.path.join(run.dir, dep)
        rel_target = os.path.relpath(target, state.run_dir)
        link = os.path.join(state.run_dir, dep)
        log.info("Linking %s", dep)
        util.ensure_dir(os.path.dirname(link))
        util.symlink(rel_target, link)
        state.manifest_entries.append(_dep_entry_for_op_link(dep, state))


def _dep_entry_for_op_link(dep, state):
    return run_manifest.generic_dependency_args(
        state.run_dir,
        dep,
        state.source_uri,
        dep,
    )


def _resolve_project_deps(deps, state):
    for dep in deps:
        if _is_project_file(dep, state):
            _copy_or_link_project_file(dep, state)
        else:
            _pull_dep(dep, state)


def _is_project_file(dep, state):
    path = os.path.join(state.project_dir, dep)
    return os.path.exists(path)


def _copy_or_link_project_file(dep, state):
    dep_path = os.path.join(state.project_dir, dep)
    if _can_copy_dep(dep_path):
        _copy_project_file(dep_path, dep, state)
    else:
        _link_project_file(dep_path, dep, state)


def _can_copy_dep(dep_path):
    return os.path.isfile(dep_path)


def _copy_project_file(src, dep, state):
    dest = os.path.join(state.run_dir, dep)
    log.info("Copying %s", dep)
    util.copyfile(src, dest)
    print(f"##### DEP 2 {src} -> {dest}")


def _link_project_file(src, dep, state):
    link = os.path.join(state.run_dir, dep)
    rel_src = os.path.relpath(src, os.path.dirname(link))
    log.info("Linking to %s", dep)
    util.symlink(rel_src, link)
    print(f"##### DEP 3 {rel_src} -> {link}")


def _pull_dep(dep, state):
    log.info("Fetching %s", dep)
    try:
        dvc_util.pull_dvc_dep(dep, state.run_dir, state.project_dir)
    except dvc_util.DvcPullError as e:
        raise SystemExit(str(e)) from e
    else:
        state.manifest_entries.append(_dep_entry_for_pull(dep, state))


def _dep_entry_for_pull(dep, state):
    return run_manifest.generic_dependency_args(
        state.run_dir,
        dep,
        state.source_uri,
        dep,
    )


def _copy_params_with_flags(state):
    for name in _iter_stage_param_files(state):
        dest = os.path.join(state.run_dir, name)
        if os.path.exists(dest):
            continue
        src = os.path.join(state.project_dir, name)
        if not os.path.exists(src):
            raise SystemExit(
                f"cannot find config file '{name}' in project "
                f"directory {state.project_dir}"
            )
        log.info("Copying %s", name)
        util.copyfile(src, dest)
        print(f"##### DEP 5 {src} -> {dest}")


def _iter_stage_param_files(state):
    seen = set()
    for _param, filename in dvc_util.iter_stage_params(
        state.target_stage, state.dvc_config
    ):
        if not filename in seen:
            seen.add(filename)
            yield filename


def _repro_run(state):
    cmd = ["dvc", "repro", "--single-item", state.target_stage]
    if not _debug_enabled():
        cmd.append("--quiet")
    log.info("Running stage '%s'", state.target_stage)
    state.manifest_entries.extend(_internal_file_entries_for_repro_cmd(state))
    p = subprocess.Popen(cmd, cwd=state.run_dir)
    returncode = p.wait()
    if returncode != 0:
        raise SystemExit(
            f"'dvc repro {util.shlex_quote(state.target_stage)}' "
            f"failed (exit code {returncode}) - see above for details"
        )


def _debug_enabled():
    return log.getEffectiveLevel() <= logging.DEBUG


def _internal_file_entries_for_repro_cmd(state):
    # Files implicitly created when running `dvc repro` - these are
    # logged as internal files so as not to be treated as generated
    relpaths = [".gitignore", "dvc.lock"]
    return [
        _internal_file_entry_for_path(
            os.path.join(state.run_dir, path),
            state,
        )
        for path in relpaths
    ]


def _log_metrics_as_summaries(state):
    with summary.SummaryWriter(state.run_dir) as events:
        for metrics_name, metrics_data in dvc_util.iter_stage_metrics_data(
            state.target_stage,
            state.run_dir,
        ):
            log.info("Logging metrics from %s", metrics_name)
            for tag, val in _iter_metrics_scalars(metrics_data):
                events.add_scalar(tag, val)


def _iter_metrics_scalars(data):
    if not isinstance(data, dict):
        return
    flattened_data = util.encode_nested_config(data)
    for name, val in flattened_data.items():
        if isinstance(val, (int, float)):
            yield name, val


def _update_run_manifest(state):
    with run_manifest.manifest_for_run(state.run_dir, mode="a") as m:
        for args in state.manifest_entries:
            m.write(args)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        op_util.handle_system_exit(e)
