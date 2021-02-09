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
Support for Dask based scehdulers

TODO: This is a stub for a Dask based queue.
"""

dask_scheduler_flags_data = yaml.safe_load(
    """
    {} # TODO: placeholder for scheduler flags def
"""
)


class DaskSchedulerProxy(object):

    name = "dask-scheduler"

    def __init__(self):
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    "dask-scheduler": {
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
        return gf.models["dask-scheduler"]

    @staticmethod
    def _init_reference():
        return modellib.ModelRef("builtin", "guildai", guild.__version__, "queue")


class DaskPlugin(pluginlib.Plugin):
    @staticmethod
    def resolve_model_op(opspec):
        if opspec in ("dask-scheduler", "dask-scheduler:dask-scheduler"):
            model = DaskSchedulerProxy()
            return model, model.name
        return None
