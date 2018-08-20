# Copyright 2017-2018 TensorHub, Inc.
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
import subprocess
import sys
import time

try:
    import psutil
except ImportError:
    this_dir = os.path.dirname(__file__)
    sys.path.append(os.path.join(this_dir, "..", "external"))
    import psutil

MIN_TIMEOUT = 5
SLEEP_INTERVAL = 60

def main():
    args = _parse_args()
    if args.timeout < MIN_TIMEOUT:
        _error("TIMEOUT must be at least %i" % MIN_TIMEOUT)
    job = _init_process(args.pidfile)
    print("Watching process %s" % job.pid)
    while True:
        _shutdown_timeout(args.timeout, args.preview)
        try:
            job.wait(SLEEP_INTERVAL)
        except psutil.TimeoutExpired:
            pass
        else:
            break
    _shutdown_timeout(args.timeout, args.preview)
    print("Process stopped, quitting")

def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "pidfile", metavar="PIDFILE",
        help="Path to file containing run process.")
    p.add_argument(
        "timeout", metavar="TIMEOUT", type=int,
        help="Shutdown timeout in minutes.")
    p.add_argument(
        "--preview", action="store_true",
        help="Preview shutdown timeouts but don't issue them.")
    return p.parse_args()

def _init_process(pidfile):
    job_pid = _job_pid(pidfile)
    return psutil.Process(job_pid)

def _job_pid(pidfile):
    try:
        raw = open(pidfile, "r").read()
    except OSError:
        _error("cannot read pid from %s" % job_file)
    else:
        return int(raw.strip())

def _shutdown_timeout(timeout, preview=False):
    cmd = ["shutdown", "+%i" % timeout, "--no-wall"]
    if preview:
        print("%s (preview)" % " ".join(cmd))
        return
    subprocess.check_call(cmd)

def _error(msg):
    sys.stderr.write("shutdown_timeout: %s\n" % msg)
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("Quitting\n")
