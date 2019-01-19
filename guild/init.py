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
import re
import os
import shutil

import yaml

from guild import util

log = logging.getLogger("guild")

class InitError(Exception):
    pass

class RequiredParamError(InitError):

    def __init__(self, name, param):
        super(RequiredParamError, self).__init__(name, param)
        self.name = name
        self.param = param

    def __str__(self):
        return "missing required parameter '%s'" % self.name

def init_env(path, local_resource_cache=False):
    init_guild_dir(os.path.join(path, ".guild"), local_resource_cache)

def init_guild_dir(path, local_resource_cache=False):
    util.ensure_dir(os.path.join(path, "runs"))
    util.ensure_dir(os.path.join(path, "trash"))
    util.ensure_dir(os.path.join(path, "cache", "runs"))
    _init_resource_cache(path, local_resource_cache)

def _init_resource_cache(guild_dir, local):
    env_cache = os.path.join(guild_dir, "cache", "resources")
    if os.path.exists(env_cache):
        log.info("Resource cache %s exists, skipping")
        return
    if local:
        if os.path.islink(env_cache):
            os.unlink(env_cache)
        util.ensure_dir(env_cache)
    else:
        shared_cache = _shared_resource_cache(guild_dir)
        util.ensure_dir(shared_cache)
        os.symlink(shared_cache, env_cache)

def _shared_resource_cache(guild_dir):
    seen = set()
    cur = os.path.dirname(guild_dir)
    while True:
        if cur in seen:
            break
        seen.add(cur)
        maybe_cache = os.path.join(cur, ".guild", "cache", "resources")
        if os.path.exists(maybe_cache):
            return maybe_cache
        cur = os.path.dirname(cur)
    return os.path.join(
        os.path.expanduser("~"),
        ".guild", "cache", "resources")

def init_project(project_dir, src, params):
    meta = _try_guild_meta(src)
    if meta:
        _validate_params(params, meta)
    to_copy = _safe_project_init_copies(src, project_dir)
    for file_src, file_dest in to_copy:
        rel_file_src = os.path.relpath(file_src, src)
        log.info("Copying %s to %s", rel_file_src, file_dest)
        util.ensure_dir(os.path.dirname(file_dest))
        shutil.copy2(file_src, file_dest)
    if meta:
        _apply_params(project_dir, params, meta)

def _try_guild_meta(src):
    meta_path = os.path.join(src, "guild.meta.yml")
    try:
        f = open(meta_path, "r")
    except IOError:
        return None
    else:
        return yaml.load(f)

def _validate_params(params, meta):
    meta_params = meta.get("params", {})
    for name, meta_param in meta_params.items():
        if meta_param.get("required") and name not in params:
            raise RequiredParamError(name, meta_param)

def _safe_project_init_copies(src, dest):
    skip_dirs = [
        ".git",
        "__pycache__",
    ]
    ignore_files = [
        re.compile(r".+\.pyc$"),
        re.compile(r"guild\.meta\.yml$"),
    ]
    safe_copies = []
    for root, dirs, files in os.walk(src):
        util.remove_all(skip_dirs, dirs)
        rel_path = root[len(src):]
        for name in files:
            if _matches(name, ignore_files):
                continue
            copy_dest = os.path.join(dest, rel_path, name)
            if os.path.exists(copy_dest):
                raise InitError(
                    "%s exists and would be overwritten"
                    % copy_dest)
            copy_src = os.path.join(root, name)
            safe_copies.append((copy_src, copy_dest))
    return safe_copies

def _matches(s, patterns):
    for p in patterns:
        if p.match(s):
            return True
    return False

def _apply_params(dest, params, meta):
    guild_file = os.path.join(dest, "guild.yml")
    lines = _read_lines(guild_file)
    if lines is not None:
        log.info("Updating %s", guild_file)
        dir_name = os.path.basename(os.path.abspath(dest))
        new_lines = [
            _replace_param_refs(line, params, meta, dir_name)
            for line in lines
        ]
        _write_lines(new_lines, guild_file)

def _read_lines(path):
    try:
        f = open(path, "r")
    except IOError:
        return None
    else:
        return list(f)

def _replace_param_refs(s, params, meta, dir_name):
    for name, meta_param in meta.get("params", {}).items():
        val = params.get(name, meta_param.get("default", ""))
        if val == "${DIR_NAME}":
            val = dir_name
        s = s.replace("{{%s}}" % name, val)
    return s

def _write_lines(lines, path):
    with open(path, "w") as f:
        for line in lines:
            f.write(line)
