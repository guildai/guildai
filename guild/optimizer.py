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

from guild import entry_point_util

_optimizers = entry_point_util.EntryPointResources(
    "guild.optimizers", "optimizer")

class NotSupported(TypeError):
    pass

class Optimizer(object):
    """Abstract interface for a Guild optimizer."""

    name = None

    def __init__(self, ep):
        self.name = ep.name
        self.log = logging.getLogger("guild." + self.name)

def iter_optimizers():
    return iter(_optimizers)

def for_name(name):
    return _optimizers.one_for_name(name)
