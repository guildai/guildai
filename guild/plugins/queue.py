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

from __future__ import absolute_import
from __future__ import division

import yaml

import guild

from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib

queue_description = """
Start a queue

A queue polls for staged runs and starts them in the order they were \
staged. By default, the queue waits for other runs to stop before \
starting any staged runs. Use `ignore-running` to bypass this check.

Use `run-once` to start staged runs and stop without waiting for new \
staged runs.
"""

queue_flags_data = yaml.safe_load(
    """
poll-interval:
  description: Minimum number of seconds between polls
  default: 10
  type: int
run-once:
  description: Run all staged runs and stop without
  default: no
  arg-switch: yes
  type: boolean
ignore-running:
  description: Start staged runs even when other runs are in-progress
  default: no
  arg-switch: yes
  type: boolean
"""
)


class QueueModelProxy(object):

    name = "queue"

    def __init__(self):
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    "queue": {
                        "description": queue_description,
                        "exec": (
                            "${python_exe} -um guild.plugins.queue_main " "${flag_args}"
                        ),
                        "flags": queue_flags_data,
                    }
                },
            }
        ]
        gf = guildfile.Guildfile(data, src="<%s>" % self.__class__.__name__)
        return gf.models["queue"]

    @staticmethod
    def _init_reference():
        return modellib.ModelRef("builtin", "guildai", guild.__version__, "queue")


class QueuePlugin(pluginlib.Plugin):
    @staticmethod
    def resolve_model_op(opspec):
        if opspec in ("queue", "queue:queue"):
            model = QueueModelProxy()
            return model, "queue"
        return None
