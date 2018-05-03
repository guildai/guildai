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

import click

from guild import click_util

def remote_arg(fn):
    click_util.append_params(fn, [
        click.Argument(("remote",))
    ])
    return fn

def remotes():
    """### Remotes

    Remotes are non-local systems that Guild can interact with. They
    are defined in ``~/.guild/config.yml`` under the ``remotes``
    section.

    Each remote must specify a ``type`` attributes. Guild currently
    supports one remote type: `ssh`.

    ### ssh remote

    An ``ssh`` remote is accessed using `ssh` and supports file copies
    using `rsync`. Both `ssh` and `rsync` programs must be installed
    and configured on the local system to run commands for this type
    of remote.

    ssh remotes support the following attributes:

    **host** - hostname of the remote system (required)

    **user** - user account on the remote host (defaults to current user)

    **guild-home** - path to Guild home relative to home directory
    associated with remote user (defaults to ``.guild``)

    """
