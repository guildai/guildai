# Copyright 2017-2022 RStudio, PBC
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

import yaml

import guild

from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib

queue_description = """
Start a queue

A queue polls for staged runs and starts them in the order they were \
staged. By default, a queue runs staged runs even if there are other \
runs in progress. To force a queue to wait until other runs finish \
before starting a staged run, set `wait-for-running` to `true` when \
starting the queue.

Use `run-once` to start staged runs and stop without waiting for \
additional staged runs.

To associate runs with one or more GPUs, set `gpus` to a comma-separated \
list of GPU IDs. This value is used when starting staged runs. For \
example, to support parallel runs on all available GPUs, start one \
queue for each GPU ID. Staged runs would then be assigned to a GPU \
according to the queue that starts it.
"""

queue_flags_data = yaml.safe_load(
    """
poll-interval:
  description: Minimum number of seconds between polls
  default: 10
  type: int
run-once:
  description: Run all staged runs and stop
  default: no
  arg-switch: yes
  type: boolean
wait-for-running:
  description: Wait for other runs to stop before starting staged runs
  default: no
  arg-switch: yes
  type: boolean
gpus:
  description: >
    Value used for gpus option when starting staged runs

    If this flag is specified and a staged run has a different value for
    gpus, the queue will not run it.
  null-label: unspecified
"""
)


class QueueModelProxy:

    name = ""

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
                            "${python_exe} -um guild.plugins.queue_main ${flag_args}"
                        ),
                        "flags": queue_flags_data,
                    }
                },
            }
        ]
        gf = guildfile.Guildfile(data, src=f"<{self.__class__.__name__}>")
        return gf.models[self.name]

    @staticmethod
    def _init_reference():
        return modellib.ModelRef("builtin", "guildai", guild.__version__, "")


class QueuePlugin(pluginlib.Plugin):
    @staticmethod
    def resolve_model_op(opspec, *_):
        if opspec in ("queue"):
            model = QueueModelProxy()
            return model, "queue"
        return None
