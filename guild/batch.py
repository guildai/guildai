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

import guild

from guild import config
from guild import guildfile
from guild import model as modellib



"""

import logging

import guild

from guild import op
from guild import opref as opreflib

log = logging.getLogger("guild")

class BatchError(Exception):
    pass

class BatchOpDefProxy(object):

    def __init__(self, child_opdef):
        self._opdef = child_opdef
        self.name = child_opdef.name
        self.fullname = child_opdef.fullname
        self.guildfile = child_opdef.guildfile
        self.modeldef = child_opdef.modeldef
        self.exec_ = "${python_exe} -um guild.batch_main"
        self.main = None
        self.steps = None
        self.env = {}
        self.disabled_plugins = []
        self.python_path = None
        self.set_trace = None
        self.handle_keyboard_interrupt = False
        self.compare = None
        self.dependencies = []
        self.label = None
        self.pre_process = None

    @staticmethod
    def flag_values(include_none=False):
        # pylint: disable=unused-argument
        return {}

    @staticmethod
    def get_flagdef(_name):
        return None

def BatchOpRef(child_op):
    return opreflib.OpRef(
        "batch", "guildai", guild.__version__, "",
        _batch_op_name(child_op))

def _batch_op_name(child_op):
    parts = ["+"]
    if child_op.opref.model_name:
        parts.extend([child_op.opref.model_name, ":"])
    parts.append(child_op.opref.op_name)
    return "".join(parts)

class Batch(op.Operation):

    def __init__(self, child_op, batch_files):
        self.child_op = child_op
        self.batch_files = batch_files
        super(Batch, self).__init__(
            opref=BatchOpRef(child_op),
            opdef=BatchOpDefProxy(child_op.opdef),
            run_dir=None,
            resource_config=None,
            extra_attrs={},
            stage_only=None,
            gpus=None)

    def init(self):
        super(Batch, self).init()
        self._init_trial_ops()

def for_op(op, batch_files):
    if batch_files or _has_batch_flag_vals(op):
        return Batch(op, batch_files)
    return None

"""
