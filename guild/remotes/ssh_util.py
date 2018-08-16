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

from guild import remote as remotelib

def ssh_ping(host, user=None, verbose=False, connect_timeout=10):
    if user:
        host = "%s@%s" % (user, host)
    cmd = ["ssh"] + _ssh_opts(verbose, connect_timeout) + [host, "true"]
    result = subprocess.call(cmd)
    if result != 0:
        raise remotelib.Down("cannot reach host %s" % host)

def ssh_cmd(host, cmd):
    cmd = ["ssh"] + _ssh_opts() + [host] + cmd
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        raise remotelib.RemoteProcessError.from_called_process_error(e)

def _ssh_opts(verbose=False, connect_timeout=None):
    opts = [
        "-oStrictHostKeyChecking=no"
    ]
    if verbose:
        opts.append("-vvv")
    if connect_timeout:
        opts.append("-oConnectTimeout=%s" % connect_timeout)
    return opts
