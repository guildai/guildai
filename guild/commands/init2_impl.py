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

import guild

from guild import cli
from guild import init
from guild import util

class Config(object):

    def __init__(self, args):
        self.env_dir = os.path.abspath(args.dir)
        self.env_name = self._init_env_name(args.name, self.env_dir)
        self.venv_python_ver = args.python
        self.guild = args.guild
        self.reqs = args.requirement
        self.tensorflow = args.tf_package
        self.local_resource_cache = args.local_resource_cache
        self.prompt_params = self._init_prompt_params()

    @staticmethod
    def _init_env_name(name, abs_env_dir):
        if name:
            return name
        elif os.path.exists(abs_env_dir):
            return os.path.basename(os.path.dirname(abs_env_dir))
        else:
            return os.path.basename(abs_env_dir)

    @staticmethod
    def _init_venv_python(arg):
        if not arg or arg.startswith("python"):
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
        if self.guild:
            params.append(("Guild version", self.guild))
        else:
            params.append(("Guild version", guild.__version__))
        if self.reqs:
            params.append(("Requirements", self.reqs))
        if self.tensorflow == "no":
            params.append(("TensorFlow support", "no"))
        elif self.tensorflow == "tensorflow":
            params.append(("TensorFlow support", "non-GPU"))
        elif self.tensorflow == "tensorflow-gpu":
            params.append(("TensorFlow support", "GPU"))
        elif self.tensorflow is None:
            params.append(("TensorFlow support", "auto-detect GPU"))
        else:
            raise AssertionError(self.tensorflow)
        if self.local_resource_cache:
            params.append(("Resource cache", "local"))
        else:
            params.append(("Resource cache", "shared"))
        return params

    def as_kw(self):
        return self.__dict__

def _shorten_path(path):
    return path.replace(os.path.expanduser("~"), "~")

def main(args):
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
    _init_guild_env(config)
    _init_venv(config)
    _install_guild(config)
    _install_cmd_reqs(config)
    _ensure_tensorflow(config)
    _initialized_msg(config)

def _init_guild_env(config):
    cli.out("Initializing Guild environment in {}".format(config.env_dir))
    init.init_env(config.env_dir, config.local_resource_cache)

def _init_venv(config):
    cmd_args = _venv_cmd_args(config)
    if not cmd_args:
        cli.out("Skipping virtual env")
        return
    cli.out("Creating virtual environment")
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

def _install_guild(config):
    """Install Guild into env.

    If the running Guild program is from `guild/scripts` (i.e. running
    in dev mode), only the Guild requirements, as defined in
    `guild/requirements.txt` are installed, under the assumption that
    `guild/scripts` is in `PATH` or an alias is being used and
    therefore Guild will be available from the env. In this case only
    the requirements need to be installed.

    If the running Guild program is not from `guild/scripts`, Guild
    will be installed using the env `pip` program.
    """
    if config.guild:
        _install_guild_dist(config)
    else:
        guild_reqs = _guild_reqs_file()
        if guild_reqs:
            _install_guild_reqs(guild_reqs, config)
        else:
            _install_default_guild_dist(config)

def _install_guild_dist(config):
    assert config.guild
    # If config.guild can be parsed as a version, use as
    # 'guildai==VERSION'
    if config.guild[0].isdigit():
        cli.out("Installing Guild %s" % config.guild)
        req = "guildai==%s" % config.guild
    else:
        cli.out("Installing %s" % req)
        req = config.guild
    _install_reqs([req], config.env_dir)

def _guild_reqs_file():
    guild_location = pkg_resources.resource_filename("guild", "")
    guild_parent = os.path.dirname(guild_location)
    path = os.path.join(guild_parent, "requirements.txt")
    try:
        f = open(path, "r")
    except OSError:
        pass
    else:
        with f:
            if "guildai" in f.readline():
                return path
    return None

def _install_guild_reqs(req_files, config):
    cli.out("Installing Guild requirements")
    _install_req_files([req_files], config.env_dir)

def _install_default_guild_dist(config):
    req = "guildai==%s" % guild.__version__
    cli.out("Installing Guild %s" % req)
    _install_reqs([req], config.env_dir)

def _install_reqs(reqs, env_dir):
    cmd_args = [_pip_bin(env_dir), "install"] + reqs
    try:
        subprocess.check_call(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _pip_bin(env_dir):
    pip_bin = os.path.join(env_dir, "bin", "pip")
    assert os.path.exists(pip_bin), pip_bin
    return pip_bin

def _install_req_files(req_files, env_dir):
    cmd_args = [_pip_bin(env_dir), "install"]
    for path in req_files:
        cmd_args.extend(["-r", path])
    try:
        subprocess.check_call(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _install_cmd_reqs(config):
    if config.reqs:
        cli.out("Installing additional requirements")
        _install_reqs(config.reqs, config.env_dir)

def _ensure_tensorflow(config):
    if config.tensorflow == "no":
        cli.out("Skipping TensorFlow installation")
        return
    if _tensorflow_installed(config.env_dir):
        cli.out("TensorFlow already installed, skipping installation")
        return
    tf_pkg = _tensorflow_package(config)
    cli.out("Installing TensorFlow (%s)" % tf_pkg)
    _install_reqs([tf_pkg], config.env_dir)

def _tensorflow_installed(env_dir):
    cli.out("Checking for TensorFlow")
    python_bin = os.path.join(env_dir, "bin", "python")
    assert os.path.exists(python_bin)
    cmd_args = [python_bin, "-c", "import tensorflow; tensorflow.__version__"]
    try:
        subprocess.check_output(cmd_args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return False
    else:
        return True

def _tensorflow_package(config):
    if config.tensorflow is not None:
        return config.tensorflow
    if util.gpu_available():
        return "tensorflow-gpu"
    else:
        return "tensorflow"

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
