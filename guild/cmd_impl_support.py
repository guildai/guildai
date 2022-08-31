# Copyright 2017-2022 RStudio, PBC
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
import typing

from guild import cli
from guild import click_util
from guild import config

# Avoid expensive or little used imports here. While this is used by
# cmd impls, which are allowed to have longer import times, many impls
# don't need the more expensive imports (e.g. guild.model,
# guild.resource - see below) and expensive imports here will apply to
# them.

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
    return f"'{cwd}'"


def cwd_guildfile(cwd=None):
    """Returns the guildfile of the context cwd.

    Returns None if a guildfile doesn't exist in the cwd.
    """
    import guild.model  # expensive

    cwd = cwd or config.cwd()
    try:
        importer = guild.model.ModelImporter(cwd)
    except ImportError:
        return None
    else:
        _check_bad_guildfile(importer.dist)
        return getattr(importer.dist, "guildfile", None)


def _check_bad_guildfile(dist):
    import guild.model  # expensive

    if isinstance(dist, guild.model.BadGuildfileDistribution):
        cli.error(
            f"guildfile in {cwd_desc(dist.location)} contains an "
            "error (see above for details)"
        )


def init_model_path(cwd=None):
    """Initializes the model path.

    If the context cwd contains a model def, the path is initialized
    to include the cwd.
    """
    import guild.model  # expensive

    _init_path(guild.model, cwd)


def init_resource_path(cwd=None):
    """Initializes the resource path.

    The same rules in `init_model_path` are applied here to the
    resource path.
    """
    import guild.resource  # expensive

    _init_path(guild.resource, cwd)


def _init_path(mod, cwd):
    cwd_gf = cwd_guildfile(cwd)
    if cwd_gf:
        mod.insert_path(cwd_gf.dir, clear_cache=True)


def one_run(runs, spec, ctx=None):
    """Returns runs[0] if len(runs) is 1 otherwise exits with an error."""
    if len(runs) == 1:
        return runs[0]
    if not runs:
        _no_matching_run_error(spec, ctx)
    _non_unique_run_id_error(runs, spec)


def _no_matching_run_error(spec, ctx) -> typing.NoReturn:
    more_help = f" or '{click_util.cmd_help(ctx)}' for more information" if ctx else ""
    cli.error(
        f"could not find a run matching '{spec}'\n"
        f"Try 'guild runs list' for a list{more_help}."
    )


def _non_unique_run_id_error(matches, spec) -> typing.NoReturn:
    cli.out(f"'{spec}' matches multiple runs:", err=True)
    for m in matches:
        cli.out(f"  {_match_short_id(m)}", err=True)
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
            cli.error(f"{_arg_desc(name, ctx)} cannot be used{error_suffix}")


def disallow_both(names, args, ctx, error_suffix=""):
    if len(names) != 2:
        raise RuntimeError("names must contain two values", names)
    a, b = names
    if getattr(args, a, False) and getattr(args, b, False):
        cli.error(
            f"{_arg_desc(a, ctx)} cannot be used with {_arg_desc(b, ctx)}{error_suffix}"
        )


def _arg_desc(name, ctx):
    for param in ctx.command.params:
        if param.name == name:
            desc = param.opts[-1]
            if desc[0] != "-":
                desc = param.human_readable_name
            return desc
    raise AssertionError(name)


def path_or_package_guildfile(path_or_package, ctx=None):
    path_or_package = path_or_package or config.cwd()
    if os.path.isdir(path_or_package):
        return _dir_guildfile(path_or_package, ctx)
    if os.path.isfile(path_or_package):
        return _guildfile(path_or_package)
    return _package_guildfile(path_or_package)


def _dir_guildfile(dir, ctx):
    from guild import guildfile

    try:
        return guildfile.for_dir(dir)
    except guildfile.NoModels:
        if ctx:
            help_suffix = f" or '{click_util.cmd_help(ctx)}' for help"
        else:
            help_suffix = ""
        cli.error(
            f"{cwd_desc(dir)} does not contain a Guild file (guild.yml)\n"
            f"Try specifying a project path or package name{help_suffix}."
        )
    except guildfile.GuildfileError as e:
        cli.error(str(e))


def _guildfile(path):
    from guild import guildfile

    try:
        return guildfile.for_file(path)
    except guildfile.GuildfileError as e:
        cli.error(str(e))


def _package_guildfile(ref):
    matches = _matching_packages(ref)
    if len(matches) == 1:
        _name, gf = matches[0]
        return gf
    if not matches:
        cli.error(
            f"cannot find a package matching '{ref}'\n"
            "Try 'guild packages' for a list of installed packages."
        )
    models_desc = ", ".join([name for name, _gf in matches])
    cli.error(
        f"multiple packages match '{ref}'\n"
        f"Try again with one of these models: {models_desc}"
    )


def _matching_packages(ref):
    from guild import model as modellib

    matches = {}
    for model in modellib.iter_models():
        if model.reference.dist_type != "package":
            continue
        name = model.reference.dist_name
        gf = model.modeldef.guildfile
        # If exact match, return one
        if ref == name:
            return [(name, gf)]
        # otherwise check for match in full name of model
        matches[name] = gf
    return sorted(matches.items())


def check_incompatible_args(incompatible, args, ctx=None):
    for val in incompatible:
        arg1_name, opt1, arg2_name, opt2 = _incompatible_arg_items(val)
        if getattr(args, arg1_name, None) and getattr(args, arg2_name):
            err_help = (
                f"\nTry '{ctx.command_path} --help' for more information."
                if ctx
                else ""
            )
            cli.error(f"{opt1} and {opt2} cannot both be specified{err_help}")


def _incompatible_arg_items(val):
    arg1, arg2 = val
    arg1, opt1 = _arg_parts(arg1)
    arg2, opt2 = _arg_parts(arg2)
    return arg1, opt1, arg2, opt2


def _arg_parts(part):
    if isinstance(part, tuple):
        assert len(part) == 2, part
        return part
    assert isinstance(part, str)
    return part, "--" + part.replace("_", "-")


def check_required_args(required, args, ctx, msg_template=None):
    msg_template = msg_template or "missing one of: %s"
    missing_args = []
    for val in required:
        arg_name, arg = _arg_parts(val)
        if getattr(args, arg_name, None):
            return
        missing_args.append(arg)
    msg = msg_template % ", ".join(missing_args)
    cli.error(f"{msg}\nTry `{ctx.command_path} --help` for more information.")


def format_warn(s):
    return cli.style(s, fg="yellow")
