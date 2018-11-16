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

import hashlib
import logging
import os
import pkg_resources
import re
import subprocess

import yaml

import guild

from guild import cli
from guild import config
from guild import init
from guild import namespace
from guild import util

log = logging.getLogger("guild")

class Config(object):

    def __init__(self, args):
        self.env_dir = os.path.abspath(args.dir)
        self.env_name = self._init_env_name(args.name, self.env_dir)
        self.venv_python = self._init_venv_python(args)
        self.guild = args.guild
        self.guild_pkg_reqs = self._init_guild_pkg_reqs(args)
        self.user_reqs = self._init_user_reqs(args)
        self.paths = args.path
        self.tensorflow = args.tf_package
        self.local_resource_cache = args.local_resource_cache
        self.prompt_params = self._init_prompt_params()
        self.no_progress = args.no_progress

    @staticmethod
    def _init_env_name(name, abs_env_dir):
        if name:
            return name
        basename = os.path.basename(abs_env_dir)
        if basename != "env":
            return basename
        return os.path.basename(os.path.dirname(abs_env_dir))

    @staticmethod
    def _init_venv_python(args):
        arg = args.python
        if not arg or arg.startswith("python"):
            return arg
        return "python{}".format(arg)

    @staticmethod
    def _init_guild_pkg_reqs(args):
        if args.no_reqs:
            return ()
        return tuple(sorted(
            _iter_all_guild_pkg_reqs(config.cwd(), args.path)))

    @staticmethod
    def _init_user_reqs(args):
        # -r options may be used with --no-reqs, in which case -r
        # takes precedence (--no-reqs may still be used to suppress
        # installation of Guild package reqs)
        if args.requirement:
            _validate_req_files(args.requirement)
            return args.requirement
        elif not args.no_reqs:
            default_reqs = os.path.join(config.cwd(), "requirements.txt")
            if os.path.exists(default_reqs):
                return (default_reqs,)
        return ()

    def _init_prompt_params(self):
        params = []
        params.append(("Location", _shorten_path(self.env_dir)))
        params.append(("Name", self.env_name))
        if self.venv_python:
            params.append(("Python interpreter", self.venv_python))
        else:
            params.append(("Python interpreter", "default"))
        if self.guild:
            params.append(("Guild version", self.guild))
        else:
            params.append(("Guild version", _implicit_guild_version()))
        if self.guild_pkg_reqs:
            params.append(("Guild package requirements", self.guild_pkg_reqs))
        if self.user_reqs:
            params.append(("Python requirements", self.user_reqs))
        if self.paths:
            params.append(("Additional paths", self.paths))
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

    def _maybe_guild_pkg_reqs(self):
        if self.no_guild_pkg_reqs:
            return []

    def as_kw(self):
        return self.__dict__

def _iter_all_guild_pkg_reqs(dir, search_path, seen=None):
    seen = seen or set()
    src = os.path.abspath(os.path.join(dir, "guild.yml"))
    if not os.path.exists(src):
        return
    if src in seen:
        return
    seen.add(src)
    for req in _guild_pkg_reqs(src):
        dir_on_path = _find_req_on_path(req, search_path)
        if dir_on_path:
            for req in _iter_all_guild_pkg_reqs(dir_on_path, search_path, seen):
                yield req
        else:
            yield req

def _guild_pkg_reqs(src):
    pkg = _pkg_for_guildfile(src)
    if not pkg:
        return []
    return _pkg_requires(pkg, src)

def _pkg_for_guildfile(src):
    data = _guildfile_data(src)
    if not isinstance(data, list):
        data = [data]
    for item in data:
        if isinstance(item, dict) and "package" in item:
            return item
    return None

def _guildfile_data(src):
    # Use low level parsing to bypass path-related errors.
    try:
        f = open(src, "r")
        return yaml.load(f)
    except Exception as e:
        log.warning(
            "cannot read Guild package requirements for %s (%s) - ignoring",
            src, e)
        return []

def _pkg_requires(pkg_data, src):
    requires = pkg_data.get("requires") or []
    if not isinstance(requires, list):
        log.warning(
            "invalid package requires list in %s (%r) - ignoring",
            src, pkg_data)
        return []
    return requires

def _find_req_on_path(req, path):
    req_subpath = req.replace(".", os.path.sep)
    for root in path:
        full_path = os.path.join(root, req_subpath)
        if os.path.exists(full_path):
            return full_path
    return None

def _validate_guild_reqs(reqs, guildfile_path):
    # Make sure we can convert each to pip reqs
    for req in reqs:
        try:
            namespace.pip_info(req)
        except namespace.NamespaceError:
            cli.error(
                "invalid required Guild package '%s' in %s\n"
                "Either correct the package name or use --no-reqs "
                "to skip installing required Guild packages"
                % (req, guildfile_path))
    return reqs

def _validate_req_files(paths):
    for p in paths:
        if not os.path.exists(p):
            cli.error("requirement file %s does not exist" % p)

def _shorten_path(path):
    return path.replace(os.path.expanduser("~"), "~")

def _implicit_guild_version():
    reqs_file = _guild_reqs_file()
    if reqs_file:
        return "from source (%s)" % os.path.dirname(reqs_file)
    else:
        return guild.__version__

def main(args):
    _error_if_active_env()
    config = Config(args)
    if args.yes or _confirm(config):
        _init(config)

def _error_if_active_env():
    active_env = os.getenv("VIRTUAL_ENV")
    if active_env:
        cli.error(
            "cannot run init from an activate environment (%s)\n"
            "Deactivate the environment by running 'deactivate' "
            "and try again."
            % active_env)

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
    _install_guild_pkg_reqs(config)
    _install_user_reqs(config)
    _install_paths(config)
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
    log.debug("venv args: %s", cmd_args)
    try:
        subprocess.check_call(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _venv_cmd_args(config):
    args = ["virtualenv", config.env_dir]
    args.extend(["--prompt", "({}) ".format(config.env_name)])
    if config.venv_python:
        args.extend(["--python", config.venv_python])
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
        cli.out("Installing %s" % config.guild)
        req = config.guild
    _install_reqs([req], config)

def _guild_reqs_file():
    guild_location = pkg_resources.resource_filename("guild", "")
    guild_parent = os.path.dirname(guild_location)
    path = os.path.join(guild_parent, "requirements.txt")
    try:
        f = open(path, "r")
    except (IOError, OSError):
        pass
    else:
        with f:
            if "guildai" in f.readline():
                return path
    return None

def _install_guild_reqs(req_files, config):
    cli.out("Installing Guild requirements")
    _install_req_files([req_files], config)

def _install_default_guild_dist(config):
    req = "guildai==%s" % guild.__version__
    cli.out("Installing Guild %s" % req)
    _install_reqs([req], config)

def _install_reqs(reqs, config):
    cmd = (
        [_pip_bin(config.env_dir), "install"] +
        _pip_extra_opts(config) +
        reqs
    )
    log.debug("pip cmd: %s", cmd)
    try:
        subprocess.check_call(cmd, env={"PATH": ""})
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _pip_bin(env_dir):
    pip_bin = os.path.join(env_dir, "bin", "pip")
    assert os.path.exists(pip_bin), pip_bin
    return pip_bin

def _pip_extra_opts(config):
    if config.no_progress:
        return ["--progress", "off"]
    else:
        return []

def _install_req_files(req_files, config):
    cmd_args = [_pip_bin(config.env_dir), "install"] + _pip_extra_opts(config)
    for path in req_files:
        cmd_args.extend(["-r", path])
    log.debug("pip cmd: %s", cmd_args)
    try:
        subprocess.check_call(cmd_args, env={"PATH": ""})
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)

def _install_guild_pkg_reqs(config):
    if config.guild_pkg_reqs:
        cli.out("Installing Python requirements")
        reqs = _pip_package_reqs(config.guild_pkg_reqs)
        _install_reqs(reqs, config)

def _pip_package_reqs(guild_reqs):
    reqs = []
    for guild_req in guild_reqs:
        pip_info = namespace.pip_info(guild_req)
        reqs.append(pip_info.project_name)
    return reqs

def _install_user_reqs(config):
    if config.user_reqs:
        cli.out("Installing Python requirements")
        _install_req_files(config.user_reqs, config)

def _install_paths(config):
    if not config.paths:
        return
    site_packages = _env_site_packages(config.env_dir)
    for path in config.paths:
        _write_path(path, site_packages)

def _env_site_packages(env_dir):
    python_bin = os.path.join(env_dir, "bin", "python")
    out = subprocess.check_output([python_bin, "-m", "site"])
    site_packages_pattern = r"(%s.+?site-packages)" % env_dir
    m = re.search(site_packages_pattern, out)
    assert m, out
    return m.group(1)

def _write_path(path, target_dir):
    path = os.path.abspath(path)
    with open(_pth_filename(target_dir, path), "w") as f:
        f.write(path)

def _pth_filename(target_dir, path):
    digest = hashlib.md5(path).hexdigest()[:8]
    pth_name = "%s-%s.pth" % (os.path.basename(path), digest)
    return os.path.join(target_dir, pth_name)

def _ensure_tensorflow(config):
    if config.tensorflow == "no":
        cli.out("Skipping TensorFlow installation")
        return
    if _tensorflow_installed(config.env_dir):
        cli.out("TensorFlow already installed, skipping installation")
        return
    tf_pkg = _tensorflow_package(config)
    cli.out("Installing TensorFlow (%s)" % tf_pkg)
    _install_reqs([tf_pkg], config)

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
