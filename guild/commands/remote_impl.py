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

import guild.remote

from guild import cli

from . import remote_support

def start(args):
    remote = remote_support.remote_for_args(args)
    if args.reinit:
        prompt = "You are about to reinitialize %s" % remote.name
        _remote_op(remote.reinit, prompt, True, args)
    else:
        prompt = "You are about to start %s" % remote.name
        _remote_op(remote.start, prompt, True, args)

def stop(args):
    remote = remote_support.remote_for_args(args)
    prompt = "WARNING: You are about to STOP %s" % remote.name
    stop_details = remote.get_stop_details()
    if stop_details:
        prompt += "\nThis will result in the following:\n"
        prompt += stop_details
    else:
        prompt += "\nThis action may result in permanent loss of data."
    _remote_op(remote.stop, prompt, False, args)

def _remote_op(op, prompt, default_resp, args):
    if not args.yes:
        cli.out(prompt)
    if args.yes or cli.confirm("Continue?", default_resp):
        try:
            op()
        except guild.remote.OperationNotSupported as e:
            cli.error(e)
        except guild.remote.OperationError as e:
            cli.error(e)

def status(args):
    remote = remote_support.remote_for_args(args)
    try:
        remote.status(args.verbose)
    except guild.remote.Down as e:
        cli.error(
            "remote %s is not available (%s)" % (remote.name, e),
            exit_status=2)
    except guild.remote.OperationError as e:
        cli.error(e)
