# Copyright 2017-2021 TensorHub, Inc.
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

dask_scheduler_description = """
Start a Dask scheduler.

Dask schedulers execute staged runs in parallel according to their \
number of workers. Specify the number of workers using the workers \
flags.

If the Bokeh Python package is installed, the schduler runs a \
dashboard application by default on port 8787. Specify a different \
port or binding address using the dashboard-address flag. To disable \
the dashboard, specify no for dashboard-address.

A Dask scheduler polls for staged runs and starts them in the order \
they were staged. Dask schedulers are queues that can process runs in \
parallel.

By default, a Dask scheduler runs staged runs even if there are other \
runs in progress. To force a scheduler to wait until other runs finish \
before starting a staged run, set wait-for-running to true when \
starting the scheduler.

Use run-once to start staged runs and stop without waiting for \
additional staged runs.
"""

dask_scheduler_flags_data = yaml.safe_load(
    """
workers:
  description: Number of workers in the Dask cluster
  type: int
loglevel:
  description: Log level used for Dask scheduler
  default: warn
  choices: [debug, info, warn, error]
dashboard-address:
  description: >
    Address to listen to for dashboard connections

    You can specify a port or an address like '0.0.0.0:8787'. Use no
    to disable the dashboard. Use 0 for a randomly assigned port.
  default: 8787
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

"""
)


class DaskModelProxy(object):

    name = "dask"

    def __init__(self):
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    "scheduler": {
                        "description": dask_scheduler_description,
                        "exec": (
                            "${python_exe} -um guild.plugins.dask_scheduler_main "
                            "${flag_args}"
                        ),
                        "flags": dask_scheduler_flags_data,
                    }
                },
            }
        ]
        gf = guildfile.Guildfile(data, src="<%s>" % self.__class__.__name__)
        return gf.models[self.name]

    @staticmethod
    def _init_reference():
        return modellib.ModelRef("builtin", "guildai", guild.__version__, "dask")


class DaskPlugin(pluginlib.Plugin):
    @staticmethod
    def resolve_model_op(opspec):
        if opspec in ("dask:scheduler",):
            model = DaskModelProxy()
            return model, "scheduler"
        return None
