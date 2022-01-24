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

import argparse
import logging
import os
import re
import shutil
import subprocess

import yaml

from guild import config
from guild import op_util
from guild import steps_util
from guild import util

from guild.commands import run_impl

log = None

PIPELINE_STAGE_PS = [
    re.compile(r"Stage '(.*?)' didn't change, skipping"),
    re.compile(r"Running stage '(.*?)':"),
]

DVC_META_NAMES = ["dvc.yaml", "dvc.lock"]


class _Pipeline:
    def __init__(self, target_stage, project_dir):
        _assert_dvc_yaml(project_dir)
        self.target_stage = target_stage
        self.project_dir = project_dir
        self.ran_stages = []
        self.dvc_yaml = _load_dvc_yaml(project_dir)
        self.parent_run = op_util.current_run()


def _assert_dvc_yaml(project_dir):
    dvc_yaml = os.path.join(project_dir, "dvc.yaml")
    if not os.path.exists(dvc_yaml):
        _missing_dvc_yaml_error(project_dir)


def _load_dvc_yaml(dir):
    with open(os.path.join(dir, "dvc.yaml")) as f:
        return yaml.safe_load(f)


def main():
    op_util.init_logging()
    globals()["log"] = logging.getLogger("guild")
    args = _init_args()
    pipeline = _Pipeline(args.stage, args.project_dir)
    if args.pipeline:
        _handle_pipeline(pipeline)
    else:
        _handle_stage(pipeline)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--pipeline", action="store_true")
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
    raise SystemExit(
        "invalid DvC config directory '%s' - missing dvc.yaml" % project_dir
    )


def _handle_pipeline(pipeline):
    for stage in _iter_pipeline_stages(pipeline):
        _assert_not_ran_pipeline_stage(stage, pipeline)
        _run_pipeline_stage(stage, pipeline)
        pipeline.ran_stages.append(stage)
    _assert_target_stage_ran(pipeline)


def _iter_pipeline_stages(pipeline):
    out = _repro_dry_run_for_pipeline(pipeline)
    for line in out.split("\n"):
        stage = _pipeline_stage_for_line(line)
        if stage:
            yield stage


def _pipeline_stage_for_line(line):
    for p in PIPELINE_STAGE_PS:
        m = p.match(line)
        if m:
            return m.group(1)
    return None


def _repro_dry_run_for_pipeline(pipeline):
    cmd = [
        "dvc",
        "repro",
        "--dry",
        pipeline.target_stage,
    ]
    log.debug("dvc repro dry run cmd: %s", cmd)
    p = subprocess.Popen(
        cmd,
        cwd=pipeline.project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    log.debug(
        "dvc repro dry run result:\n%s---\n%s---\n%i",
        util.lazy_str(lambda: _decode(out)),
        util.lazy_str(lambda: _decode(err)),
        p.returncode,
    )
    if p.returncode != 0:
        _dvc_pipeline_status_error(err, p.returncode)
    assert not err, (err, out)
    return _decode(out)


def _decode(s):
    return s.decode("utf-8", errors="ignore") if s is not None else None


def _dvc_pipeline_status_error(err_raw, returncode):
    assert err_raw is not None
    err = _decode(err_raw).strip()
    raise SystemExit("error getting DvC pipeline status: %s (%i)" % (err, returncode))


def _assert_not_ran_pipeline_stage(stage, pipeline):
    if stage in pipeline.ran_stages:
        ran_desc = ", ".join(pipeline.ran_stages)
        raise SystemExit(
            "cycle detected in pipeline stages: trying to run "
            "'%s' but already ran %s" % (stage, ran_desc)
        )


def _run_pipeline_stage(stage, pipeline):
    stage_run = _init_stage_run(stage, pipeline)
    env = _stage_env()
    with config.SetCwd(pipeline.project_dir):
        with util.Env(env, replace=True):
            run_impl.run(opspec="dvc.yaml:%s" % stage, run_dir=stage_run.dir)


def _init_stage_run(stage, pipeline):
    stage_run = steps_util.init_step_run(pipeline.parent_run.dir)
    steps_util.link_to_step_run(stage, stage_run.dir, pipeline.parent_run.dir)
    return stage_run


def _stage_env():
    env = dict(os.environ)
    env["NO_WARN_RUNDIR"] = "1"
    return env


def _assert_target_stage_ran(pipeline):
    if pipeline.target_stage not in pipeline.ran_stages:
        ran_desc = ", ".join(pipeline.ran_stages)
        raise SystemError(
            "failed to run target stage '%s' in pipeline %s"
            % (pipeline.target_stage, ran_desc)
        )


def _handle_stage(pipeline):
    stage_outputs = _target_stage_outputs(pipeline)
    log.info("Running DvC stage %s", pipeline.target_stage)
    _repro_run_for_pipeline(pipeline)
    _copy_dvc_meta_to_run_dir(pipeline.project_dir)
    _copy_stage_outputs_to_run_dir(stage_outputs, pipeline.project_dir)


def _target_stage_outputs(pipeline):
    stage_data = pipeline.dvc_yaml.get("stages", {}).get(pipeline.target_stage, {})
    return stage_data.get("outs", [])


def _repro_run_for_pipeline(pipeline):
    cmd = [
        "dvc",
        "repro",
        pipeline.target_stage,
    ]
    log.debug("dvc repro cmd: %s", cmd)
    log.debug("dvc repro cwd: %s", pipeline.project_dir)
    p = subprocess.Popen(cmd, cwd=pipeline.project_dir)
    returncode = p.wait()
    if returncode != 0:
        raise SystemExit(
            "'dvc repro %s' failed (exit code %i) - see above for details"
            % (util.shlex_quote(pipeline.target_stage), returncode)
        )


def _copy_dvc_meta_to_run_dir(source_dir):
    run_dir = _required_run_dir()
    for name in DVC_META_NAMES:
        src = os.path.join(source_dir, name)
        if not os.path.exists(src):
            log.warning(
                "DvC meta file %s does not exist in %s - "
                "cannot copy to Guild run directory",
                name,
                source_dir,
            )
            continue
        log.debug("copying stage output '%s' to run directory '%s'", src, run_dir)
        log.info("Copying %s", name)
        shutil.copy(src, run_dir)


def _copy_stage_outputs_to_run_dir(outputs, source_dir):
    run_dir = _required_run_dir()
    for path in outputs:
        src = os.path.join(source_dir, path)
        log.debug("copying stage output '%s' to run directory '%s'", src, run_dir)
        log.info("Copying %s", path)
        shutil.copy(src, run_dir)


def _required_run_dir():
    run_dir = os.getenv("RUN_DIR")
    if not run_dir:
        raise SystemExit("missing required environment RUN_DIR for operation")
    return run_dir


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        op_util.handle_system_exit(e)
