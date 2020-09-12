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

import logging
import os
import sys
import threading

# Avoid expensive imports - config is used by commands.main and any
# time here is applied to all commands.

log = logging.getLogger("guild")

_cwd = None
_cwd_lock = threading.Lock()
_guild_home = None
_guild_home_lock = threading.Lock()
_log_output = False
_user_config = None


class ConfigError(Exception):
    pass


def set_cwd(cwd):
    globals()["_cwd"] = cwd


class SetCwd(object):

    _save = None

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        _cwd_lock.acquire()
        self._save = cwd()
        set_cwd(self.path)

    def __exit__(self, *_args):
        set_cwd(self._save)
        _cwd_lock.release()


class SetGuildHome(object):

    _save = None

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self._save = guild_home()
        if self.path:
            set_guild_home(self.path)

    def __exit__(self, *_args):
        set_guild_home(self._save)


def set_guild_home(path):
    with _guild_home_lock:
        globals()["_guild_home"] = path


def cwd():
    return _cwd or "."


def guild_home():
    with _guild_home_lock:
        maybe_home = _guild_home
    return maybe_home or default_guild_home()


def default_guild_home():
    try:
        return os.environ["GUILD_HOME"]
    except KeyError:
        base = _default_guild_home_base()
        return os.path.realpath(os.path.join(base, ".guild"))


def _default_guild_home_base():
    return _find_apply([_conda_home, _virtualenv_home, _user_home])


def _conda_home():
    return os.getenv("CONDA_PREFIX")


def _virtualenv_home():
    return os.getenv("VIRTUAL_ENV")


def _user_home():
    return os.path.expanduser("~")


def set_log_output(flag):
    globals()["_log_output"] = flag


def log_output():
    return _log_output


class _Config(object):
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
    import six  # See note above about imports.

    try:
        parent_specs = item.pop("extends")
    except KeyError:
        pass
    else:
        if isinstance(parent_specs, six.string_types):
            parent_specs = [parent_specs]
        for spec in parent_specs:
            parent = _resolved_parent(spec, section, data, src)
            _apply_parent(parent, item)


def _resolved_parent(spec, section, data, src):
    parent = _find_parent(spec, section, data)
    if parent is None:
        raise ConfigError("cannot find '%s' in %s" % (spec, src))
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


def user_config():
    path = user_config_path()
    config = _user_config
    if config is None or config.path != path:
        config = _Config(path)
        globals()["_user_config"] = config
    return config.read()


def user_config_path():
    try:
        return os.environ["GUILD_CONFIG"]
    except KeyError:
        return os.path.join(os.path.expanduser("~"), ".guild", "config.yml")


def user_config_home():
    return os.path.dirname(user_config_path())


def python_exe():
    return _find_apply(
        [
            _guild_python_exe,
            _conda_python_exe,
            _virtualenv_python_exe,
            _sys_executable,
        ]
    )


def _guild_python_exe():
    return os.getenv("GUILD_PYTHON_EXE")


def _conda_python_exe():
    conda_prefix = os.getenv("CONDA_PREFIX")
    if not conda_prefix:
        return None
    return _find_apply(
        [_this_conda_python_exe, _default_conda_python_exe], conda_prefix
    )


def _this_conda_python_exe(conda_prefix):
    if sys.executable.startswith(conda_prefix):
        return sys.executable
    return None


def _default_conda_python_exe(conda_prefix):
    python_exe = os.path.join(conda_prefix, "bin", "python")
    if os.path.exists(python_exe):
        return python_exe
    return None


def _virtualenv_python_exe():
    try:
        env_path = os.environ["VIRTUAL_ENV"]
    except KeyError:
        return None
    else:
        maybe_python_exe = os.path.join(env_path, "bin", "python")
        return maybe_python_exe if os.path.exists(maybe_python_exe) else None


def _sys_executable():
    return sys.executable


def _find_apply(funs, *args):
    # Move util.find_apply here to defer import of util - see note
    # above about imports.
    from guild import util

    return util.find_apply(funs, *args)
