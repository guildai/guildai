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
import subprocess

from guild import config
from guild import op_util

from guild.commands import run_impl

log = None  # init in main

PIPELINE_STAGE_P = re.compile(r"Running stage '(.*?)':")


class _Pipeline:
    def __init__(self, target_stage, config_dir):
        self.target_stage = target_stage
        self.config_dir = config_dir


def main():
    op_util.init_logging()
    globals()["log"] = logging.getLogger()
    args = _init_args()
    _assert_dvc_yaml(args.config_dir)
    pipeline = _Pipeline(args.stage, args.config_dir)
    if args.pipeline:
        _handle_pipeline(pipeline)
    else:
        _handle_stage(pipeline)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--pipeline", action="store_true")
    p.add_argument("config_dir")
    p.add_argument("stage")
    return p.parse_args()


def _assert_dvc_yaml(config_dir):
    dvc_yaml = os.path.join(config_dir, "dvc.yaml")
    if not os.path.exists(dvc_yaml):
        _missing_dvc_yaml_error(config_dir)


def _missing_dvc_yaml_error(config_dir):
    raise SystemExit(
        "invalid DvC config directory '%s' - missing dvc.yaml" % config_dir
    )


def _handle_pipeline(pipeline):
    for stage in _iter_pipeline_stages(pipeline):
        _run_pipeline_stage(stage, pipeline)


def _iter_pipeline_stages(pipeline):
    out = _repro_dry_run_for_pipeline(pipeline)
    for line in out.split("\n"):
        stage = _pipeline_stage_for_line(line)
        if stage:
            yield stage


def _pipeline_stage_for_line(line):
    m = PIPELINE_STAGE_P.match(line)
    return m.group(1) if m else None


def _repro_dry_run_for_pipeline(pipeline):
    cmd = [
        "dvc",
        "repro",
        "--dry",
        pipeline.target_stage,
    ]
    log.debug("getting dvc pipeline status cmd: %s", cmd)
    p = subprocess.Popen(
        cmd,
        cwd=pipeline.config_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    if p.returncode != 0:
        _dvc_pipeline_status_error(err, p.returncode)
    assert not err, (err, out)
    return out.decode("utf-8", errors="ignore")


def _dvc_pipeline_status_error(err_raw, returncode):
    err = err_raw.decode("utf-8", errors="ignore").strip()
    raise SystemExit("error getting DvC pipeline status: %s (%i)" % (err, returncode))


def _run_pipeline_stage(stage, pipeline):
    with config.SetCwd(pipeline.config_dir):
        run_impl.run(opspec="__dvc__:%s" % stage)


def _handle_stage(pipeline):
    print(
        "TODO: actually run the stage %s from %s"
        % (pipeline.target_stage, pipeline.config_dir)
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        op_util.handle_system_exit(e)
