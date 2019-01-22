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

class OutputScalars(object):

    def __init__(self, _config, run):
        # TODO: compile regexes from config
        #self._writer = _init_writer(run)
        pass

    def write(self, _out):
        # TODO: lazily create writer as needed
        # TODO: apply regexes to out to get key, val, and optional step
        #self._writer.add_scalar("foo", 1.123, 0)
        pass

    def close(self):
        #self._writer.close()
        pass

def _init_writer(run):
    import tensorboardX
    return tensorboardX.SummaryWriter(run.guild_path())
