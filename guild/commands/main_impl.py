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

import logging
import os

from guild import cli
from guild import config
from guild import log
from guild import util

def main(args):
    log.init_logging(args.log_level or logging.INFO)
    config.set_cwd(_validated_dir(args.cwd))
    config.set_guild_home(
        _validated_dir(args.guild_home, abs=True, create=True))

def _validated_dir(path, abs=False, create=False):
    path = os.path.expanduser(path)
    if abs:
        path = os.path.abspath(path)
    if not os.path.exists(path):
        if create:
            util.ensure_dir(path)
        else:
            cli.error("directory '%s' does not exist" % path)
    if not os.path.isdir(path):
        cli.error("'%s' is not a directory" % path)
    return path
