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

import os

from guild import util

def init_env(path, local_resource_cache=False):
    guild_dir = os.path.join(path, ".guild")
    util.ensure_dir(os.path.join(guild_dir, "dist-packages"))
    util.ensure_dir(os.path.join(guild_dir, "pkg"))
    util.ensure_dir(os.path.join(guild_dir, "runs"))
    util.ensure_dir(os.path.join(guild_dir, "trash"))
    util.ensure_dir(os.path.join(guild_dir, "cache", "runs"))
    user_resource_cache = os.path.join(
        os.path.expanduser("~"), ".guild", "cache", "resources")
    env_resource_cache = os.path.join(guild_dir, "cache", "resources")
    if local_resource_cache or not os.path.isdir(user_resource_cache):
        if os.path.islink(env_resource_cache):
            os.unlink(env_resource_cache)
        util.ensure_dir(env_resource_cache)
    elif not os.path.exists(env_resource_cache):
        os.symlink(user_resource_cache, env_resource_cache)
