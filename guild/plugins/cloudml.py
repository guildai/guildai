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
import re
import shlex
import subprocess
import sys

from guild import plugin
from guild import plugin_util

class Training(object):

    def __init__(self, args, log):
        job_args, flag_args = self._parse_args(args)
        self.run = plugin_util.current_run()
        self.job_name = job_args.job_name or self._job_name()
        self.job_dir = "gs://%s/%s" % (job_args.bucket_name, self.job_name)
        self.runtime_version = job_args.runtime_version
        self.module_name = job_args.module_name
        self.package_path = job_args.package_path
        self.region = job_args.region
        self.flag_args = flag_args
        self.package_name = self._package_name()
        self.package_version = self._package_version()
        self.log = log

    @staticmethod
    def _parse_args(args):
        p = argparse.ArgumentParser()
        p.add_argument("--region", required=True)
        p.add_argument("--bucket-name", required=True)
        p.add_argument("--job-name")
        p.add_argument("--runtime-version")
        p.add_argument("--module-name", required=True)
        p.add_argument("--package-path")
        p.add_argument("--data-dir")
        return p.parse_known_args(args)

    def _job_name(self):
        return "guild_run_%s" % self.run.id

    def _package_name(self):
        from guild.opref import OpRef
        opref = OpRef.from_run(self.run)
        return opref.model_name

    def _package_version(self):
        return "0.0.0+%s" % self.run.short_id

    def write_run_attrs(self):
        self.run.write_attr("cloudml-job-name", self.job_name)
        self.run.write_attr("cloudml-job-dir", self.job_dir)

    def upload_data(self):
        src = self.run.path
        dest = self.job_dir
        subprocess.check_call(
            ["/usr/bin/gsutil", "-m", "cp", "-r", src, dest])
        # Work around for gutils decision to not follow links
        # inrecursive copies (see
        # https://github.com/GoogleCloudPlatform/gsutil/issues/412)
        for root, dirs, _files in os.walk(src):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if os.path.islink(dir_path):
                    rel_path = dir_path[len(src):]
                    dest_dir_path = dest + rel_path
                    subprocess.check_call(
                        ["/usr/bin/gsutil", "-m", "cp", "-r",
                         dir_path, dest_dir_path])

    def init_package(self):
        env = {
            "PYTHONPATH": os.path.pathsep.join(sys.path),
            "PACKAGE_NAME": self.package_name,
            "PACKAGE_VERSION": self.package_version,
        }
        # Use an external process as setuptools assumes it's a command
        # line app
        subprocess.check_call(
            [sys.executable, "-um", "guild.plugins.training_pkg_main"],
            env=env,
            cwd=self.run.path)

    def submit_job(self):
        args = [
            "/usr/bin/gcloud", "ml-engine", "jobs",
            "submit", "training", self.job_name,
            "--job-dir", self.job_dir,
            "--packages", self._find_package_name(),
            "--module-name", self.module_name,
            "--region", self.region,
        ]
        if self.runtime_version:
            args.extend(["--runtime-version", self.runtime_version])
        if self.package_path:
            args.extend(["--package-path", self.package_path])
        if self.flag_args:
            args.append("--")
            args.extend(self._resolved_flag_args())
        self.log.info("Starting job %s in %s", self.job_name, self.job_dir)
        self.log.debug("gutil cmd: %r", args)
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _resolved_flag_args(self):
        subs = [
            ("${job-dir}", self.job_dir),
            ("${job-name}", self.job_name),
        ]
        def resolve(val):
            for pattern, sub in subs:
                val = val.replace(pattern, sub)
            return val
        return [resolve(arg) for arg in self.flag_args]

    def _find_package_name(self):
        package_name = re.sub(r"[^0-9a-zA-Z]+", "_", self.package_name)
        path = "%s-%s-py2.py3-none-any.whl" % (package_name, self.package_version)
        assert os.path.exists(path), path
        return path

    def write_lock(self):
        with open(self.run.guild_path("LOCK.remote"), "w") as f:
            f.write("cloudml:job:%s" % self.job_name)

    def watch_logs(self):
        args = [
            "/usr/bin/gcloud", "ml-engine", "jobs",
            "stream-logs", self.job_name
        ]
        try:
            subprocess.call(args)
        except KeyboardInterrupt:
            pass

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
        training = Training(args, self.log)
        training.write_run_attrs()
        training.upload_data()
        training.init_package()
        training.submit_job()
        training.write_lock()
        training.watch_logs()
