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

import os

import guild.cli
import guild.click_util
import guild.model
import guild.modelfile

def init_model_path(args, ctx):
    if not args.all:
        guild.model.set_path([])
    maybe_model_src = _find_model_source(_cwd(ctx))
    if maybe_model_src:
        guild.model.add_model_source(maybe_model_src)

def iter_models(args, ctx):
    init_model_path(args, ctx)
    models = list(guild.model.iter_models())
    if not models:
        _no_models_error(ctx)
    return models

def _handle_no_models(args):
    if args.all:
        cli.out("There are no models installed on this system.")
    else:
        cli.out(
            "There are no models defined in this directory.\n"
            "Try a different directory or specify --all to list all "
            "installed models.")
    cli.error()

def _find_model_source(path):
    # Note that the order of NAMES matters as the first match is used
    # over subsequent names.
    for name in guild.modelfile.NAMES:
        filename = os.path.join(path, name)
        if os.path.isfile(filename):
            return filename
    return None

def modelfile(ctx):
    try:
        return guild.modelfile.from_dir(_cwd(ctx))
    except (guild.modelfile.NoModels, IOError):
        _no_models_error(ctx)

def _no_models_error(ctx):
    cmd_path = ctx.command_path.split(" ")
    guild.cli.error(
        "this directory does not contain any models\n"
        "Try a different directory with '%s -C DIR %s' "
        "or '%s' for more information."
        % (cmd_path[0], " ".join(cmd_path[1:]),
           guild.click_util.cmd_help(ctx)))

def _cwd(ctx):
    return ctx.obj["cwd"]

"""
import os

import guild.cli
import guild.click_util
import guild.package
import guild.modelfile
import guild.util

class NoModelfile(Exception):
    pass

def project_for_location(location, ctx=None):
    project = find_project_for_location(location)
    if project is None:
        _no_project_error(location, ctx)
    return project

def find_project_for_location(location):
    location = location or "."
    try:
        return _project_for_location(location)
    except NoModelfile:
        return None

def _project_for_location(location):
    try:
        return guild.modelfile.from_file_or_dir(location)
    except (guild.modelfile.NoModels, IOError):
        raise NoModelfile()

def _no_project_error(location, ctx):
    location = project_location_option(location) or "."
    msg_parts = []
    if os.path.exists(location):
        msg_parts.append(
            "%s does not contain any models\n"
            % project_location_desc(location))
    else:
        msg_parts.append("%s does not exist\n" % location)
    msg_parts.append(try_project_location_help(location, ctx))
    guild.cli.error("".join(msg_parts))

def project_location_desc(location):
    location = project_location_option(location)
    return ("%s" % location if location
            else "the current directory")

def try_project_location_help(location, ctx=None):
    location = project_location_option(location)
    help_parts = []
    if location:
        help_parts.append("Try specifying a different location")
    else:
        help_parts.append("Try specifying a project location")
    if ctx:
        help_parts.append(
            " or '%s' for more information."
            % guild.click_util.ctx_cmd_help(ctx))
    else:
        help_parts.append(".")
    return "".join(help_parts)

def project_location_option(location):
    location = os.path.abspath(location or "")
    basename = os.path.basename(location)
    if basename in ["MODEL", "MODELS", "__generated__"]:
        location = os.path.dirname(location)
    if location == os.getcwd():
        return ""
    else:
        return location

def split_pkg(pkg):
    try:
        return guild.package.split_name(pkg)
    except guild.package.NamespaceError as e:
        namespaces = ", ".join(
            [name for name, _ in guild.namespace.iter_namespaces()])
        guild.cli.error(
        "unknown namespace '%s' in %s\n"
        "Supported namespaces: %s"
        % (e.value, pkg, namespaces))
"""
