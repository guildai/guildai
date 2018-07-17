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
import pkg_resources
import subprocess

from guild import cli

class Config(object):

    def __init__(self, args):
        self.env_dir = os.path.abspath(args.dir)
        self.env_name = self._init_env_name(args.name, self.env_dir)
        self.venv_python_ver = args.python
        self.reqs = args.requirement
        self.prompt_params = self._init_prompt_params()

    @staticmethod
    def _init_env_name(name, abs_env_dir):
        if name:
            return name
        return os.path.basename(os.path.dirname(abs_env_dir))

    @staticmethod
    def _init_venv_python(arg):
        if not arg or arg.startswith("python") :
            return arg
        return "python{}".format(arg)

    def _init_prompt_params(self):
        params = []
        params.append(("Location", _shorten_path(self.env_dir)))
        params.append(("Name", self.env_name))
        if self.venv_python_ver:
            params.append(("Python version", self.venv_python_ver))
        else:
            params.append(("Python version", "default"))
        if self.reqs:
            params.append(("Requirements", self.reqs))
        return params

    def as_kw(self):
        return self.__dict__

def _shorten_path(path):
    return path.replace(os.path.expanduser("~"), "~")

def main(args, ctx):
    config = Config(args)
    if args.yes or _confirm(config):
        _init(config)

def _confirm(config):
    cli.out("You are about to initialize a Guild environment:")
    for name, val in config.prompt_params:
        if isinstance(val, tuple):
            cli.out("  {}:".format(name))
            for x in val:
                cli.out("    {}".format(x))
        else:
            cli.out("  {}: {}".format(name, val))
    return cli.confirm("Continue?", default=True)

def _init(config):
    _init_venv(config)
    _install_guild_reqs(config)
    _install_reqs(config)
    _initialized_msg(config)

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
    args = ["virtualenv", config.env_dir]
    args.extend(["--prompt", "({}) ".format(config.env_name)])
    if config.venv_python_ver:
        args.extend(["--python", "python{}".format(config.venv_python)])
    return args

def _install_guild_reqs(config):
    """Install Guild requirements.txt if running from source."""
    guild_reqs = _guild_reqs_file()
    if os.path.exists(guild_reqs):
        cli.out("Installing Guild requirements")
        _install_reqs_([guild_reqs], config.env_dir)

def _guild_reqs_file():
    guild_location = pkg_resources.resource_filename("guild", "")
    guild_parent = os.path.dirname(guild_location)
    return os.path.join(guild_parent, "requirements.txt")

def _install_reqs(config):
    if config.reqs:
        cli.out("Installing project requirements")
        _install_reqs_(config.reqs, config.env_dir)

def _install_reqs_(reqs, env_dir):
    pip_bin = os.path.join(env_dir, "bin", "pip")
    if not os.path.exists(pip_bin):
        pip_bin = "pip"
    cmd_args = [pip_bin, "install"]
    for path in reqs:
        cmd_args.extend(["-r", path])
    try:
        subprocess.check_call(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _initialized_msg(config):
    cli.out(
        "Guild environment initialized in {}."
        "\n".format(_shorten_path(config.env_dir)))
    cli.out("To activate it " "run:\n")
    env_parent = os.path.dirname(config.env_dir)
    if env_parent != os.getcwd():
        cli.out("  source guild-env {}".format(config.env_dir))
    else:
        env_name = os.path.basename(config.env_dir)
        if env_name != "env":
            cli.out("  source guild-env {}".format(env_name))
        else:
            cli.out("  source guild-env")
    cli.out()

def _source_cmd(env_dir):
    name = os.path.basename(env_dir)
    if name == "env":
        return "source guild-env"
    else:
        return "source guild-env {}".format(name)
