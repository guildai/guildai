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

import guild.remote

class SSHRemote(guild.remote.Remote):

    def __init__(self, config):
        self.host = config["host"]
        self.user = config.get("user")
        self.guild_home = config.get("guild-home")

    def push(self, runs):
        print("TODO: push %i run(s) to %s" % (len(runs), self.host))
