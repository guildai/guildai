# Copyright 2017-2020 TensorHub, Inc.
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

import os

import filelock

from guild import config
from guild import util


# filelock uses `info` level logging for acquire/release status - move
# this to debug level.
filelock.logger().info = filelock.logger().debug

Timeout = filelock.Timeout

RUN_STATUS = "run-status"


def Lock(name, timeout=-1, guild_home=None):
    guild_home = guild_home or config.guild_home()
    locks_dir = os.path.join(guild_home, "locks")
    util.ensure_dir(locks_dir)
    lock_path = os.path.join(locks_dir, name)
    return filelock.FileLock(lock_path, timeout)
