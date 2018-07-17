# Copyright 2017-2018 TensorHub, Inc.
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

import os
import subprocess

from guild import cli

class Config(object):

    def __init__(self, args):
        self.env_dir = os.path.join(".", args.dir)
        self.venv_type = args.type
        self.venv_python = args.python
        self.prompt_params = self._init_prompt_params()

    def _init_prompt_params(self):
        params = []
        params.append(("Location", self.env_dir))
        if self.venv_type == "venv":
            params.append(("Virtual environment", "yes"))
        elif args.venv_type == "none":
            params.append(("Virtual environment", "no"))
        else:
            assert self.venv_type
        if self.venv_type != "none":
            if self.venv_python:
                params.append(("Python", self.venv_type))
            else:
                params.append(("Python", "default"))
        return params

    def as_kw(self):
        return self.__dict__

def main(args, ctx):
    config = Config(args)
    if args.yes or _confirm(config):
        _init(config)

def _confirm(config):
    cli.out("You are about to initialize a Guild environment:")
    for name, val in config.prompt_params:
        cli.out("  {}: {}".format(name, val))
    return cli.confirm("Continue?", default=True)

def _init(config):
    _init_venv(config)

def _init_venv(config):
    cmd_args = _venv_cmd_args(config)
    if not cmd_args:
        cli.out("Skipping virtual env")
        return
    try:
        subprocess.check_call(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _venv_cmd_args(config):
    if config.venv_type == "venv":
        return _virtualenv_cmd_args(config)
    elif config.venv_type == "none":
        return None
    else:
        assert config.venv_type

def _virtualenv_cmd_args(config):
    args = ["virtualenv", config.env_dir]
    if config.venv_python:
        args.extend(["--python", config.venv_python])
    return args
