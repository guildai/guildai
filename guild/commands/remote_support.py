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
    """### Remotes

    A remote must be defined in ``~/.guild/config.yml`` under the
    ``remotes`` top-level section. Each remote must specify a ``type``
    attribute that specifies the type of remote. Remotes may provide
    additional attributes as configuration.

    Support remote types include are listed below.

    **ssh** - remote is accessible via `ssh` and `rsync`. An `ssh`
    remote must specify a ``host`` and may additionally specify
    ``user`` and ``guild-home``. By default `user` is the current user
    and `guild-home` is ``~/.guild``. The programs `ssh` and `rsync`
    must both be installed and configured correct on the system to
    support ssh remotes. User authentication is handled by ssh using
    identities (private keys) - password authentication is not
    supported.

    """
    click_util.append_params(fn, [
        click.Argument(("remote",))
    ])
    return fn
