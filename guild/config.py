# Copyright 2017-2023 Posit Software, PBC
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

import logging
import os
import sys
import threading

# Avoid expensive imports - config is used by commands.main and any
# time here is applied to all commands.

log = logging.getLogger("guild")

_cwd = os.path.curdir
_cwd_lock = threading.Lock()
_guild_home = None
_guild_home_lock = threading.Lock()
_log_output = False
_user_config = None


class ConfigError(Exception):
    pass


def set_cwd(cwd):
    """Sets cwd for Guild.

    The current directory for Guild is different from `os.getcwd()` as
    it's specified by the user (or a user proxy) as a Guild-specific
    current directory.

    Guild maintains the distinction between `cwd` and the process
    current directory to provide meaningful user messages. If Guild
    changes the process directory (i.e. a call to `os.chdir()`),
    messages to users could no longer reflect the user-facing current
    directory.

    Consider this comment:

        $ guild -C my-project run train

    To the user, this is equivalent to `cd my-project; guild run
    train`. However, Guild can't use this technique internally to run
    the command because it needs to preserve the user-facing cwd for
    messages. E.g. an error in the project Guild file is in
    `my-project/guild.yml` from the user's perspective. If Guild used
    `os.chdir('my-poject')` it would no longer be able to show the
    correct path to the user.
    """
    with _cwd_lock:
        globals()["_cwd"] = cwd


def cwd():
    """Returns cwd for Guild.

    See `set_cwd()` for details on Guild's current directory vs the
    process current directory (i.e. `os.getcwd()`).
    """
    with _cwd_lock:
        return _cwd or os.getcwd()


class SetCwd:
    _save = None

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self._save = cwd()
        set_cwd(self.path)

    def __exit__(self, *_args):
        set_cwd(self._save)


def set_guild_home(path):
    with _guild_home_lock:
        globals()["_guild_home"] = path
        if path is None:
            os.environ.pop("GUILD_HOME", None)
        else:
            os.environ["GUILD_HOME"] = path


def guild_home():
    return _explicitly_set_guild_home() or default_guild_home()


def _explicitly_set_guild_home():
    with _guild_home_lock:
        return _guild_home


def default_guild_home():
    return _guild_home_env() or _guild_home_for_scheme()


def _guild_home_env():
    return os.environ.get("GUILD_HOME")


def _guild_home_for_scheme():
    scheme = _guild_home_scheme()
    if scheme == "pre-0.9":
        return _guild_home_pre_0_9()
    if scheme:
        log.warning(
            "unsupported legacy scheme for 'guild-home': %r - using default scheme",
            scheme,
        )
    return _guild_home_current_scheme()


def _guild_home_scheme():
    return os.getenv("GUILD_HOME_SCHEME") or _guild_scheme_for_user_config()


def _guild_scheme_for_user_config():
    # Only check user home config for `legacy` setting as the default
    # `user_config()` relies on Guild home (which we're trying to find
    # at this point)
    config = user_config(_methods=[_user_home_user_config])
    return config.get("legacy", {}).get("guild-home")


def _guild_home_pre_0_9():
    base = _find_apply([_conda_home, _virtualenv_home, _user_home])
    return os.path.realpath(os.path.join(base, ".guild"))


def _conda_home():
    return os.getenv("CONDA_PREFIX") or None


def _virtualenv_home():
    return os.getenv("VIRTUAL_ENV") or None


def _user_home():
    return os.path.expanduser("~")


def _guild_home_current_scheme():
    """Returns the Guild home directory using the current scheme.

    The current scheme checks for Guild home in two locations:

    - Under an activated virtual environment
    - In `.guild` from the current directory up to user home

    """
    return _explicit_activated_env_guild_home() or _dot_guild_for_cwd()


def _explicit_activated_env_guild_home():
    """Returns the path to `.guild` for an acticated env."""
    activated_env = _find_apply([_conda_home, _virtualenv_home])
    if not activated_env:
        return None
    maybe_guild_home = os.path.realpath(os.path.join(activated_env, ".guild"))
    if not os.path.isdir(maybe_guild_home):
        return None
    return maybe_guild_home


def _dot_guild_for_cwd():
    """Returns the path to `.guild` for the current directory.

    If the current directory doesn't contain `.guild`, applies the
    scheme to the parent directory up until the user home
    directory. If `.guild` does not exist in any of the directories,
    returns the real path to `~/.guild`.
    """

    from guild import file_util

    user_home = _user_home()
    existing = file_util.find_up(
        ".guild",
        start_dir=cwd(),
        stop_dir=user_home,
        check=os.path.isdir,
    )
    return existing or os.path.join(user_home, ".guild")


class SetGuildHome:
    _save_attr = None
    _save_env = None

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self._save_attr = _guild_home
        self._save_env = os.getenv("GUILD_HOME")
        set_guild_home(self.path)

    def __exit__(self, *_args):
        with _guild_home_lock:
            globals()["_guild_home"] = self._save_attr
            if self._save_env is None:
                os.environ.pop("GUILD_HOME", None)
            else:
                os.environ["GUILD_HOME"] = self._save_env


def set_log_output(flag):
    globals()["_log_output"] = flag


def log_output():
    return _log_output


class _Config:
    def __init__(self, path):
        self.path = path
        self._data = None
        self._mtime = 0

    def read(self):
        if self._data is None or self._path_mtime() > self._mtime:
            self._data = self._parse()
            _apply_config_inherits(self._data, self.path)
            self._mtime = self._path_mtime()
        return self._data

    def _path_mtime(self):
        try:
            return os.path.getmtime(self.path)
        except (IOError, OSError):
            return 0

    def _parse(self):
        import yaml  # somewhat expensive

        try:
            f = open(self.path, "r")
        except IOError as e:
            if e.errno != 2:  # file not found
                log.warning("cannot read user config in %s: %s", self.path, e)
        else:
            try:
                return yaml.safe_load(f) or {}
            except Exception as e:
                log.warning("error loading user config in %s: %s", self.path, e)
        return {}


def _apply_config_inherits(data, src):
    for name, section in data.items():
        if name != "config" and isinstance(section, dict):
            _apply_section_inherits(section, data, src)
    data.pop("config", None)


def _apply_section_inherits(section, data, src):
    for _name, item in sorted(section.items()):
        if isinstance(item, dict):
            _apply_section_item_inherits(item, section, data, src)


def _apply_section_item_inherits(item, section, data, src):
    try:
        parent_specs = item.pop("extends")
    except KeyError:
        pass
    else:
        if isinstance(parent_specs, str):
            parent_specs = [parent_specs]
        for spec in parent_specs:
            parent = _resolved_parent(spec, section, data, src)
            _apply_parent(parent, item)


def _resolved_parent(spec, section, data, src):
    parent = _find_parent(spec, section, data)
    if parent is None:
        raise ConfigError(f"cannot find '{spec}' in {src}")
    parent_item, parent_section = parent
    _apply_section_item_inherits(parent_item, parent_section, data, src)
    return parent_item


def _find_parent(spec, section, data):
    return _find_apply([_section_item, _config_item], spec, section, data)


def _section_item(spec, section, _data=None):
    try:
        item = section[spec]
    except KeyError:
        return None
    else:
        return item, section


def _config_item(spec, _section, data):
    return _section_item(spec, data.get("config", {}))


def _apply_parent(parent, target):
    if not isinstance(parent, dict) or not isinstance(target, dict):
        return
    for parent_attr, parent_val in parent.items():
        try:
            target_val = target[parent_attr]
        except KeyError:
            target[parent_attr] = parent_val
        else:
            if isinstance(parent_val, dict) and isinstance(target_val, dict):
                _apply_parent(parent_val, target_val)


class SetUserConfig:
    _save = None

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        self._save = user_config
        globals()["user_config"] = lambda _methods: self.data

    def __exit__(self, *exc):
        globals()["user_config"] = self._save


def user_config(_methods=None):
    path = user_config_path(_methods)
    config = _user_config
    if config is None or config.path != path:
        config = _Config(path)
        globals()["_user_config"] = config
    return config.read()


def user_config_path(_methods=None):
    return _find_apply(
        _methods or [
            _env_user_config,
            _cwd_user_config,
            _guild_home_user_config,
            _user_home_user_config,
        ]
    )


def _env_user_config():
    return os.environ.get("GUILD_CONFIG")


def _cwd_user_config():
    path = os.path.join(cwd(), "guild-config.yml")
    return path if os.path.exists(path) else None


def _guild_home_user_config():
    path = os.path.join(guild_home(), "config.yml")
    return path if os.path.exists(path) else None


def _user_home_user_config():
    return os.path.join(os.path.expanduser("~"), ".guild", "config.yml")


def user_config_home():
    return os.path.dirname(user_config_path())


def python_exe():
    return _find_apply([
        _guild_python_exe,
        _virtualenv_python_exe,
        _sys_executable,
    ])


def _guild_python_exe():
    return os.getenv("GUILD_PYTHON_EXE")


def _virtualenv_python_exe():
    if not _virtual_env_activated():
        return None
    from guild import util  # See import note above

    return util.which("python")


def _virtual_env_activated():
    virtual_env_prefix = _virtual_env_prefix()
    return virtual_env_prefix and _python_bin_exists(virtual_env_prefix)


def _virtual_env_prefix():
    return os.getenv("VIRTUAL_ENV") or os.getenv("CONDA_PREFIX")


def _python_bin_exists(prefix):
    return os.path.exists(os.path.join(prefix, "bin", "python"))


def _sys_executable():
    return sys.executable


def _find_apply(funs, *args):
    # Move util.find_apply here to defer import of util - see note
    # above about imports.
    from guild import util

    return util.find_apply(funs, *args)


class ConfigValue:
    _unread = object()

    def __init__(self, attr_path, default):
        self.attr_path = attr_path
        self.default = default
        self._val = self._unread

    def read(self, no_cache=False):
        if not no_cache and self._val is not self._unread:
            return self._val
        try:
            self._val = _read_config_value(self.attr_path)
        except KeyError:
            self._val = self.default
        return self._val


def _read_config_value(attr_path):
    cur = user_config()
    for name in attr_path:
        cur = cur[name]
    return cur
