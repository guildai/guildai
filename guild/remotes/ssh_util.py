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

import subprocess

import guild.remote

def ssh_ping(host, verbose=False):
    cmd = ["ssh"] + _ssh_opts(verbose) + [host, "true"]
    result = subprocess.call(cmd)
    if result != 0:
        raise guild.remote.Down("cannot reach host %s" % host)

def _ssh_opts(verbose):
    opts = [
        "-oStrictHostKeyChecking=no"
    ]
    if verbose:
        opts.append("-vvv")
    return opts
