# Copyright 2017-2020 TensorHub, Inc.
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
import sys

import six
import yaml

import guild

from guild import cli
from guild import config
from guild import guildfile
from guild import init
from guild import pip_util
from guild import util

log = logging.getLogger("guild")

PYTHON_REQ_P = re.compile(r"^\s*#\s*python(\S+?)\s*$", re.MULTILINE)


class Config(object):
    def __init__(self, args):
        self.env_dir = os.path.abspath(args.dir)
        self.env_name = self._init_env_name(args.name, self.env_dir)
        self.guild = args.guild
        self.guild_home = self._init_guild_home(args)
        self.no_isolate = args.no_isolate
        self.user_reqs = self._init_user_reqs(args)
        self.guild_pkg_reqs = self._init_guild_pkg_reqs(args)
        self.venv_python = self._init_venv_python(args, self.user_reqs)
        self.paths = args.path
        self.system_site_packages = args.system_site_packages
        self.isolate_resources = args.isolate_resources
        self.pre_release = args.pre_release
        self.prompt_params = self._init_prompt_params()
        self.no_progress = args.no_progress

    @staticmethod
    def _init_env_name(name, abs_env_dir):
        if name:
            return name
        basename = os.path.basename(abs_env_dir)
        if basename != "venv":
            return basename
        return os.path.basename(os.path.dirname(abs_env_dir))

    @staticmethod
    def _init_guild_home(args):
        if args.guild_home:
            return args.guild_home
        if args.no_isolate:
            return config.guild_home()
        return None

    @staticmethod
    def _init_venv_python(args, user_reqs):
        if args.python:
            return _python_interpreter_for_arg(args.python)
        return _suggest_python_interpreter(user_reqs)

    @staticmethod
    def _init_guild_pkg_reqs(args):
        if args.no_reqs:
            return ()
        reqs = list(_iter_all_guild_pkg_reqs(config.cwd(), args.path))
        return tuple(sorted(reqs))

    @staticmethod
    def _init_user_reqs(args):
        # -r options may be used with --no-reqs, in which case -r
        # takes precedence (--no-reqs may still be used to suppress
        # installation of Guild package reqs)
        if args.requirement:
            return args.requirement
        elif not args.no_reqs:
            default_reqs = os.path.join(config.cwd(), "requirements.txt")
            if os.path.exists(default_reqs):
                return (default_reqs,)
        return ()

    def _init_prompt_params(self):
        params = []
        params.append(("Location", util.format_dir(self.env_dir)))
        params.append(("Name", self.env_name))
        if self.venv_python:
            params.append(("Python interpreter", self.venv_python))
        else:
            params.append(("Python interpreter", "default"))
        params.append(
            ("Use system site packages", "yes" if self.system_site_packages else "no")
        )
        if self.guild:
            params.append(("Guild", self.guild))
        else:
            params.append(("Guild", _implicit_guild_version()))
        if self.guild_home:
            params.append(("Guild home", self.guild_home))
        if self.guild_pkg_reqs:
            params.append(("Guild package requirements", self.guild_pkg_reqs))
        if self.user_reqs:
            params.append(("Python requirements", self.user_reqs))
        if self.pre_release:
            params.append(("Use pre-release", "yes"))
        if self.paths:
            params.append(("Additional paths", self.paths))
        if self.isolate_resources:
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
    src = os.path.abspath(guildfile.guildfile_path(dir))
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
    pkg = _guildfile_pkg(src)
    if not pkg:
        return []
    return _pkg_requires(pkg, src)


def _guildfile_pkg(src):
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
        return yaml.safe_load(f)
    except Exception as e:
        log.warning(
            "cannot read Guild package requirements for %s (%s) - ignoring", src, e
        )
        return []


def _pkg_requires(pkg_data, src):
    requires = pkg_data.get("requires") or []
    if isinstance(requires, six.string_types):
        requires = [requires]
    if not isinstance(requires, list):
        log.warning(
            "invalid package requires list in %s (%r) - ignoring", src, pkg_data
        )
        return []
    return requires


def _find_req_on_path(req, path):
    req_subpath = req.replace(".", os.path.sep)
    for root in path:
        full_path = os.path.join(root, req_subpath)
        if os.path.exists(full_path):
            return full_path
    return None


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
            "and try again." % active_env
        )


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
    _test_symlinks()
    _init_guild_env(config)
    _init_venv(config)
    _upgrade_pip(config)
    _install_guild(config)
    _install_guild_pkg_reqs(config)
    _install_user_reqs(config)
    _install_paths(config)
    _initialized_msg(config)


def _test_symlinks():
    """If Windows, confirm that user can create symbolic links."""
    try:
        util.test_windows_symlinks()
    except OSError:
        cli.error(
            "this command requires symbolic link privilege on Windows\n"
            "Try running this command with administrator privileges."
        )


def _init_guild_env(config):
    cli.out("Initializing Guild environment in {}".format(config.env_dir))
    try:
        init.init_env(config.env_dir, config.guild_home, config.isolate_resources)
    except init.PermissionError as e:
        cli.error("unable to write to %s - do you have write permission?" % e.args[0])
    except init.InitError as e:
        cli.error(e)


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
    args = _venv_cmd_base_args() + [config.env_dir]
    args.extend(["--prompt", "({}) ".format(config.env_name)])
    if config.venv_python:
        args.extend(["--python", config.venv_python])
    if config.system_site_packages:
        args.append("--system-site-packages")
    return args


def _venv_cmd_base_args():
    return util.find_apply([_virtualenv_cmd, _virtualenv_missing_error])


def _virtualenv_cmd():
    return util.find_apply([_virtualenv_module_cmd, _virtualenv_script_cmd])


def _virtualenv_module_cmd():
    try:
        import virtualenv as _
    except ImportError:
        return None
    else:
        return [sys.executable, "-m", "virtualenv"]


def _virtualenv_script_cmd():
    cmd = util.which("virtualenv")
    if not cmd:
        return None
    return [cmd]


def _virtualenv_missing_error():
    cli.error(
        "cannot find virtualenv\n" "Try installing it with 'pip install virtualenv'."
    )


def _upgrade_pip(config):
    cmd_args = _pip_bin_args(config.env_dir) + ["install", "--upgrade", "pip"]
    cli.out("Upgrading pip")
    log.debug("pip upgrade cmd: %s", cmd_args)
    try:
        subprocess.check_output(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)


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
    # Install Guild dist ignoring installed. In some cases (behavior
    # seems to have landed in pip 19.3.1) pip will decide not to
    # install the Guild req if it's already installed outside the
    # virtual env. The --ignore-installed flag in this case forces pip
    # to actually install Guild.
    _install_reqs([req], config, ignore_installed=True)


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
    _install_reqs([req_files], config)


def _install_default_guild_dist(config):
    req = "guildai==%s" % guild.__version__
    cli.out("Installing Guild %s" % req)
    _install_reqs([req], config)


def _pip_bin_args(env_dir):
    if util.get_platform() == "Windows":
        python_bin = os.path.join(env_dir, "Scripts", "python.exe")
    else:
        python_bin = os.path.join(env_dir, "bin", "python")
    assert os.path.exists(python_bin), python_bin
    return [python_bin, "-m", "pip"]


def _pip_extra_install_opts(config):
    opts = []
    if config.no_progress:
        opts.extend(["--progress", "off"])
    if config.pre_release:
        opts.append("--pre")
    return opts


def _install_reqs(reqs, config, ignore_installed=False):
    cmd_args = (
        _pip_bin_args(config.env_dir)
        + ["install", "--no-warn-script-location"]
        + _pip_extra_install_opts(config)
    )
    if ignore_installed:
        cmd_args.append("--ignore-installed")
    for req in reqs:
        if _is_requirements_file(req):
            cmd_args.extend(["-r", req])
        else:
            cmd_args.append(req)
    log.debug("pip cmd: %s", cmd_args)
    try:
        _check_call_with_empty_env(cmd_args)
    except subprocess.CalledProcessError as e:
        cli.error(str(e), exit_status=e.returncode)


def _check_call_with_empty_env(args):
    """Pass through to subprocess.check_call with empty env.

    There is surprising behavior on macOS Python 3x during init where
    a pip install command from outside a virtual environment - which
    should install a package correctly in the environment - installs
    the package but uses the wrong path to Python in installed package
    shell command shebangs. The result is that package shell scripts
    (e.g. the `guild` command) will use the wrong Python version. This
    surprising behavior appears to be related to something in the
    environment.

    Setting the command env to an empty dict corrects this problem and
    ensures that pip installed packages use the correct Python
    path. Note that setting env to None does not correct the problem.

    Update: macOS Python 2.7 has issues when PATH is not in the env so
    we set it to the value of the current PATH env.
    """
    env = {"PATH": os.getenv("PATH")}
    subprocess.check_call(args, env=env)


def _is_requirements_file(path):
    if not os.path.isfile(path):
        return False
    return pip_util.is_requirements(path)


def _install_guild_pkg_reqs(config):
    if config.guild_pkg_reqs:
        cli.out("Installing Guild package requirements")
        _install_reqs(config.guild_pkg_reqs, config)


def _install_user_reqs(config):
    if config.user_reqs:
        cli.out("Installing Python requirements")
        _install_reqs(config.user_reqs, config)


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


def _python_interpreter_for_arg(arg):
    if arg.startswith("python"):
        return arg
    # Assume arg is a version
    return "python{}".format(arg)


def _suggest_python_interpreter(user_reqs):
    """Returns best guess Python interpreter.

    We look for a Python requirement in two places: a package def in
    cwd Guild file and user requirements, which includes
    requirements.txt by default.

    A Python spec can be provided in a requirements file using a
    special `python<spec>` comment. E.g. `python>=3.5`.
    """
    python_requires = util.find_apply(
        [
            _python_requires_for_pkg,
            lambda: _python_requires_for_reqs(user_reqs),
        ]
    )
    if not python_requires:
        return None
    matching = util.find_python_interpreter(python_requires)
    if matching:
        _path, ver = matching
        return "python%s" % ver
    return None


def _python_requires_for_pkg():
    pkg_data = _guildfile_pkg_data()
    if not pkg_data:
        return None
    return pkg_data.get("python-requires")


def _guildfile_pkg_data():
    src = guildfile.guildfile_path()
    if not os.path.exists(src):
        return None
    data = _guildfile_data(src)
    for top_level in data:
        if isinstance(top_level, dict) and "package" in top_level:
            return top_level
    return None


def _python_requires_for_reqs(reqs):
    for req_file in reqs:
        try:
            s = open(req_file, "r").read()
        except IOError:
            pass
        else:
            m = PYTHON_REQ_P.search(s)
            if m:
                return m.groups(1)
    return None


def _initialized_msg(config):
    cli.out(
        "Guild environment initialized in {}."
        "\n".format(util.format_dir(config.env_dir))
    )
    cli.out("To activate it " "run:\n")
    cli.out("  %s" % _source_cmd(config.env_dir))
    cli.out()


def _source_cmd(env_dir):
    if os.path.exists(os.path.join(env_dir, "Scripts", "activate.bat")):
        return _windows_activate_cmd(env_dir)
    else:
        return _default_source_cmd(env_dir)


def _windows_activate_cmd(env_dir):
    return os.path.join(env_dir, "Scripts", "activate")


def _default_source_cmd(env_dir):
    env_parent = os.path.dirname(env_dir)
    if env_parent != os.getcwd():
        return "source guild-env {}".format(env_dir)
    else:
        env_name = os.path.basename(env_dir)
        if env_name == "venv":
            return "source guild-env"
        else:
            return "source guild-env {}".format(env_name)
