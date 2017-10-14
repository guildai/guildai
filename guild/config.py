# Copyright 2017 TensorHub, Inc.
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

import errno
import os

import yaml

import guild.var

def load_config():
    try:
        f = open(config_source_path(), "r")
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return {}
    else:
        with f:
            return yaml.load(f)

def config_source_path():
    return guild.var.path("config.yml")

def write_config(config):
    filename = config_source_path()
    _ensure_dir(filename)
    with open(filename, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

def _ensure_dir(filename):
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
