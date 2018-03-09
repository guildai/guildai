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

import logging
import os

from guild import cli
from guild import click_util
from guild import config

# Avoid expensive imports here. While this is used by cmd impls, which
# are allowed to have longer import times, many impls don't need the
# more expensive imports (e.g. guild.model, guild.resource - see
# below) and expensive imports here will apply to them.

log = logging.getLogger("guild")

def cwd_desc(cwd=None):
    """Returns a description for cwd.

    If cwd the system cwd, returns "this directory" otherwise returns
    the quoted cwd.

    This is used in messages to the user where the cwd is referenced.
    """
    cwd = cwd or config.cwd()
    if os.path.abspath(cwd) == os.path.abspath(os.getcwd()):
        return "the current directory"
    else:
        return "'%s'" % cwd

def cwd_guildfile(cwd=None):
    """Returns the guildfile of the context cwd.

    Returns None if a guildfile doesn't exist in the cwd.
    """
    import guild.model # expensive
    cwd = cwd or config.cwd()
    try:
        importer = guild.model.ModelImporter(cwd)
    except ImportError:
        return None
    else:
        _check_bad_guildfile(importer.dist)
        return getattr(importer.dist, "guildfile", None)

def _check_bad_guildfile(dist):
    import guild.model # expensive
    if isinstance(dist, guild.model.BadGuildfileDistribution):
        cli.error(
            "guildfile in %s contains error (see above for details)"
            % cwd_desc(dist.location))

def init_model_path(args, cwd=None):
    """Initializes the model path.

    If the context cwd contains a model def, the path is initialized
    so that only models associated with the cwd are available via
    `guild.model`. An exception to this is when `force_all` is true,
    in which case all models including those in the cwd will be
    available.
    """
    import guild.model # expensive
    _init_path(guild.model, "models", args, cwd)

def init_resource_path(args, cwd=None):
    """Initializes the resource path.

    The same rules in `init_model_path` are applied here to the
    resource path.
    """
    import guild.resource # expensive
    _init_path(guild.resource, "resources", args, cwd)

def _init_path(mod, desc, args, cwd):
    cwd_mf = cwd_guildfile(cwd)
    if cwd_mf:
        if args.all:
            mod.insert_path(cwd_mf.dir)
        else:
            _notify_path_limited(cwd, desc)
            mod.set_path([cwd_mf.dir])

def _notify_path_limited(path, what):
    cli.note_once(
        "Limiting %s to %s (use --all to include all)"
        % (what, cwd_desc(path)))

def one_run(runs, spec, ctx=None):
    """Returns runs[0] if len(runs) is 1 otherwise exits with an error."""
    if len(runs) == 1:
        return runs[0]
    if not runs:
        _no_matching_run_error(spec, ctx)
    _non_unique_run_id_error(runs, spec)

def _no_matching_run_error(spec, ctx):
    help_msg = (
        " or '%s' for more information" % click_util.cmd_help(ctx)
        if ctx else "")
    cli.error(
        "could not find run matching '%s'\n"
        "Try 'guild runs list' for a list%s."
        % (spec, help_msg))

def _non_unique_run_id_error(matches, spec):
    cli.out("'%s' matches multiple runs:" % spec, err=True)
    for m in matches:
        cli.out("  %s" % _match_short_id(m), err=True)
    cli.error()

def _match_short_id(m):
    # A match can be a run or a tuple of run_id, path
    try:
        return m.short_id
    except AttributeError:
        run_id, _path = m
        return run_id[:8]

def disallow_args(names, args, ctx, error_suffix=""):
    for name in names:
        if getattr(args, name, False):
            cli.error(
                "%s cannot be used%s"
                % (_arg_desc(name, ctx), error_suffix))

def disallow_both(names, args, ctx, error_suffix=""):
    if len(names) != 2:
        raise RuntimeError("names must contain two values", names)
    a, b = names
    if getattr(args, a, False) and getattr(args, b, False):
        cli.error(
            "%s cannot be used with %s%s"
            % (_arg_desc(a, ctx), _arg_desc(b, ctx), error_suffix))

def _arg_desc(name, ctx):
    for param in ctx.command.params:
        if param.name == name:
            desc = param.opts[-1]
            if desc[0] != "-":
                desc = param.human_readable_name
            return desc
    raise AssertionError(name)
