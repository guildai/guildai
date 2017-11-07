# Copyright 2017 TensorHub, Inc.
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
import os
import shlex
import subprocess
import sys

import guild.run

from guild import plugin
from guild import plugin_util

class CloudMLPlugin(plugin.Plugin):

    def enabled_for_op(self, op):
        parts = shlex.split(op.cmd)
        if parts[0] != "@cloudml:train":
            return False, "operation not supported by plugin"
        return True, ""

    def run_op(self, op_spec, args):
        if op_spec == "train":
            self._train(args)
        else:
            raise plugin.NotSupported(op_spec)

    def _train(self, args):
        job_args, flag_args = self._parse_args(args)
        run = plugin_util.current_run()
        job_name = job_args.job_name or self._job_name_for_run(run)
        job_dir = "gs://%s/%s" % (job_args.bucket_name, job_name)
        self._copy(run.path, job_dir)
        self._init_cloudml_run_attrs(job_name, job_dir, run)
        self._submit_training(
            job_name, job_dir, job_args.runtime_version,
            job_args.module_name, job_args.region, job_args.package_path,
            flag_args)
        self._write_remote_lock(run)

    @staticmethod
    def _parse_args(args):
        p = argparse.ArgumentParser()
        p.add_argument("--region", required=True)
        p.add_argument("--bucket-name", required=True)
        p.add_argument("--job-name")
        p.add_argument("--runtime-version", default="1.2")
        p.add_argument("--module-name", required=True)
        p.add_argument("--package-path")
        return p.parse_known_args(args)

    @staticmethod
    def _job_name_for_run(run):
        return "guild_run_%s" % run.id

    @staticmethod
    def _copy(src, dest):
        subprocess.check_call(
            ["/usr/bin/gsutil", "-m", "cp", "-r", src, dest])
        # Work around the fact gutils doesn't follow links (see
        # https://github.com/GoogleCloudPlatform/gsutil/issues/412)
        for root, dirs, files in os.walk(src):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if os.path.islink(dir_path):
                    rel_path = dir_path[len(src):]
                    dest_dir_path = dest + rel_path
                    subprocess.check_call(
                        ["/usr/bin/gsutil", "-m", "cp", "-r",
                         dir_path, dest_dir_path])

    @staticmethod
    def _init_cloudml_run_attrs(job_name, job_dir, run):
        run.write_attr("cloudml-job-name", job_name)
        run.write_attr("cloudml-job-dir", job_dir)

    def _submit_training(self, job_name, job_dir, runtime_version,
                         module_name, region, package_path, flag_args):
        args = [
            "/usr/bin/gcloud", "ml-engine", "jobs",
            "submit", "training", job_name,
            "--job-dir", job_dir,
            "--runtime-version", runtime_version,
            "--module-name", module_name,
            "--region", region,
        ]
        if package_path:
            args.extend(["--package-path", package_path])
        if flag_args:
            args.append("--")
            args.extend(flag_args)
        self.log.info("Starting job %s in %s", job_name, job_dir)
        self.log.debug("gutil cmd: %r" % args)
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @staticmethod
    def _write_remote_lock(run):
        with open(run.guild_path("LOCK.remote"), "w") as f:
            f.write("plugin:cloudml")
