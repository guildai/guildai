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

dask_scheduler_description = """
Start a Dask scheduler.

Dask schedulers execute staged runs in parallel according to their \
number of workers. Specify the number of workers using the workers \
flags. The default worker count is based on the number of CPU cores \
available on the system.

A Dask scheduler polls for staged runs and starts them in the order \
they were staged.

You can specify a set of available resources for a scheduler using the \
resources flag. A resource is a named quantity that is made available \
to a run. When a run requires a resource, it specifies the required \
quantity using a tag in the format 'dask:NAME=QUANTITY'. If that \
quantity is not available to the scheduler, the run waits until the \
quantity is available. When started, the run temporarily depletes its \
required quantity from the scheduler. When the run finishes, it \
replenishes the depleted quantity. In this way, resources limit what \
is run by a scheduler to avoid resource exhaustion. \

Resources can be used to constrain runs by available memory, GPUs, \
disk space or any other resource type including abstract resources \
like job size or user quotas.

Resources are specified using name value pairs in the format \
NAME=VALUE. Multiple resources are specified by separating name value \
pairs with whitespace.

Use run-once to start staged runs and stop without waiting for \
additional staged runs.

By default, a Dask scheduler runs staged runs even if there are other \
runs in progress. To force a scheduler to wait until other runs finish \
before starting a staged run, set wait-for-running to true when \
starting the scheduler.

If the Bokeh Python package is installed, the schduler runs a \
dashboard application by default on port 8787. Specify a different \
port or binding address using the dashboard-address flag. To disable \
the dashboard, specify no for dashboard-address.
"""

dask_scheduler_flags_data = yaml.safe_load(
    """
workers:
  description: >
    Number of workers in the Dask cluster

    By default, the cluster uses one worker per CPU core available on
    the system.
  null-label: auto
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
resources:
  description: >
    Set of resource levels available to the scheduler

    Use this flag to specify resources for the scheduler. When runs
    are staged with a tag in the format 'dask:<resources>', each run
    depletes a resource by the value specified in the tag. For
    example, if a scheduler is started with 'resources=MEM=5e9' and a
    run is staged with a tag value 'dask:MEM=1e9', the 'MEM' resource
    is reduced by 1e9 for that run. When the run is completed, the
    depleted resource is restored to the scheduler.

    If a run is staged with required resources that are not defined
    for the scheduler, the scheduler does not start the run.
  null-label: unconstrained
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
