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

import guild.remote

log = logging.getLogger("guild.remotes.tpu")

class TPURemote(guild.remote.Remote):

    def __init__(self, name, config):
        self.name = name
        log.info("TODO: config from %s", config)

    def start(self):
        log.info("TODO: ensure node started")

    def stop(self):
        log.info("TODO: ensure node stopped")

    def status(self, verbose=False):
        log.info("TODO: print status")

    def push(self, runs, delete=False):
        raise NotImplementedError()

    def pull(self, runs, delete=False):
        raise NotImplementedError()

    def pull_all(self, verbose=False):
        raise NotImplementedError()

    def pull_src(self):
        raise NotImplementedError()
