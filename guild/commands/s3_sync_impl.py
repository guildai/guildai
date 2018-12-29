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

import subprocess
import re
import time

from guild import cli
from guild import util
from guild import var

from . import service_impl_support

NAME = "s3-sync"
TITLE = "S3 sync service"

class State(object):

    def __init__(self, runs_dir, s3_uri, log):
        self.runs_dir = runs_dir
        self.s3_uri = s3_uri
        self.log = log

def start(args):
    _check_cli()
    run = lambda log: _run(args, log)
    service_impl_support.start(
        NAME, run, args, TITLE,
        log_max_size=(args.log_max_size * 1024 * 1024),
        log_backups=args.log_backups)

def _check_cli():
    if not util.which("aws"):
        cli.error(
            "%s requires the AWS Command Line Interface\n"
            "Refer to https://docs.aws.amazon.com/cli/latest/"
            "userguide/installing.html for details."
            % NAME)

def _run(args, log):
    assert args.sync_interval >= 5, args
    log.info("%s started", TITLE)
    runs_dir = var.runs_dir()
    s3_uri = _s3_uri(args)
    log.info("Synchronizing %s with runs in %s", s3_uri, runs_dir)
    state = State(runs_dir, s3_uri, log)
    sync_once = lambda: _sync_once(state)
    util.loop(sync_once, time.sleep, args.sync_interval, 0)

def _s3_uri(args):
    m = re.match(r"s3://([^/]+)(.*)", args.uri)
    if not m:
        cli.error("URI must be in the format s3://BUCKET[/PATH]")
    bucket, path = m.groups()
    if path[-1:] == "/":
        path = path[:-1]
    if path:
        return "s3://{}/{}".format(bucket, path)
    else:
        return "s3://{}".format(bucket)

def _sync_once(state):
    log = state.log
    log.info("Sync started")
    cmd = [
        "aws", "s3", "sync",
        "--delete",
        "--size-only",
        "--no-progress",
        state.runs_dir,
        state.s3_uri + "/runs/"]
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1)
    while True:
        line = p.stdout.readline()
        if not line:
            break
        log.info(line[:-1].decode())
    log.info("Sync stopped")

def stop():
    service_impl_support.stop(NAME, TITLE)

def status():
    service_impl_support.status(NAME, TITLE)
