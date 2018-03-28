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
import sys

import click
import yaml

import guild

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import init
from guild import pip_util
from guild import util

from guild.commands import check

log = logging.getLogger("guild")

def main(args, ctx):
    if args.list_templates:
        _list_templates()
        return
    if args.help_template:
        _help_template(args.help_template)
        return
    _maybe_shift_first_param(args)
    if args.project_artifact == "project" or args.from_package:
        _init_project(args, ctx)
    elif args.env:
        assert args.project_artifact is None, args
        initialized = _init_env(args, ctx)
        if initialized and not args.no_check:
            _check_env(args)
    else:
        cli.error(
            "specify either --env, --project, or --from-package\n"
            "Try 'guild init --help' for more information.")

def _list_templates():
    templates_home = _project_templates_home()
    data = []
    for name in sorted(os.listdir(templates_home)):
        meta = _load_project_template(os.path.join(templates_home, name))
        data.append({
            "name": name,
            "description": util.strip_trailing_period(
                meta.get("description", ""))
        })
    cli.table(data, ["name", "description"])

def _project_templates_home():
    return os.path.join(guild.__pkgdir__, "guild", "templates", "projects")

def _load_project_template(template_dir):
    meta_path = os.path.join(template_dir, "guild.meta.yml")
    return yaml.load(open(meta_path, "r"))

def _help_template(name):
    template_dir = os.path.join(_project_templates_home(), name)
    try:
        meta = _load_project_template(template_dir)
    except IOError as e:
        if e.errno != 2: # not found
            raise
        cli.error(
            "cannot find template '%s'\n"
            "Try 'guild init --list-templates' for a list of "
            "available templates."
            % name)
    out = click.HelpFormatter()
    out.write_text("Project template: %s" % name)
    out.write_paragraph()
    out.indent()
    out.write_text(meta.get("description", ""))
    out.dedent()
    params = meta.get("params", {})
    if params:
        out.write_paragraph()
        out.write_heading("Parameters")
        params_dl = [
            (param_name, _template_param_help(params[param_name]))
            for param_name in sorted(params)
        ]
        out.indent()
        out.write_dl(params_dl)
    cli.out("".join(out.buffer))

def _template_param_help(param):
    help = []
    help.append(param.get("description", ""))
    try:
        default_val = param["default"]
    except KeyError:
        if param.get("required", False):
            help.append("(required)")
    else:
        help.append("(default is '%s')" % default_val)
    return " ".join(help)

def _maybe_shift_first_param(args):
    if args.dir and "=" in args.dir:
        args.params = (args.dir,) + args.params
        args.dir = None

def _init_project(args, ctx):
    cmd_impl_support.disallow_args(
        ["local_resource_cache"],
        args, ctx, " with --project")
    cmd_impl_support.disallow_both(
        ("template", "from_package"),
        args, ctx)
    dir = args.dir or "."
    dir_desc = cmd_impl_support.cwd_desc(dir)
    if args.from_package:
        src = _package_source(args.from_package)
        src_desc = "%s package" % args.from_package
    else:
        template = args.template or "default"
        src = _project_template_source(template)
        src_desc = "%s template" % template
    prompt = (
        "You are about to initialize a project in %s\n"
        "Continue?" % dir_desc)
    if args.yes or cli.confirm(prompt, default=True):
        cli.out("Initializing project in %s using %s" % (dir_desc, src_desc))
        try:
            init.init_project(dir, src, _init_params(args))
        except init.RequiredParamError as e:
            cli.error(
                "missing required '%s' parameter\n"
                "Add %s=VALUE to the command and try again."
                % (e.name, e.name))
        except init.InitError as e:
            cli.error(e)

def _package_source(pkg):
    if os.path.exists(pkg):
        return pkg
    import pkg_resources # expensive
    try:
        dist = pkg_resources.get_distribution("gpkg." + pkg)
    except pkg_resources.DistributionNotFound:
        cli.error("cannot find package '%s' - is it installed?" % pkg)
    else:
        return os.path.join(dist.location, dist.key.replace(".", os.path.sep))

def _project_template_source(template):
    if os.path.exists(template):
        return template
    template_path = os.path.join(_project_templates_home(), template)
    if not os.path.exists(template_path):
        cli.error(
            "cannont find template '%s'\n"
            "Try 'guild init --list-templates' for a list."
            % template)
    return template_path

def _init_params(args):
    return {
        name: val for name, val in [_split_param(p) for p in args.params]
    }

def _split_param(val):
    if "=" not in val:
        cli.error(
            "invalid parameter '%s' - must be in "
            "the form NAME=VALUE" % val)
    return val.split("=", 1)

def _init_env(args, ctx):
    cmd_impl_support.disallow_args(
        ["params", "template", "from_package"],
        args, ctx, " when initializing an environment")
    env_path = os.path.abspath(args.dir or os.path.dirname(config.guild_home()))
    prompt = (
        "You are about to initialize a Guild AI environment in %s\n"
        "Continue?" % env_path)
    if args.yes or cli.confirm(prompt, default=True):
        cli.out("Initialzing Guild environment in %s" % env_path)
        init.init_env(env_path, args.local_resource_cache)
        return True
    return False

def _check_env(args):
    _check_tensorflow(args)
    _check_guild()

def _check_tensorflow(args):
    tf = _try_load_tensorflow()
    if tf:
        cli.out("TensorFlow version %s installed" % tf.__version__)
    else:
        cli.out(cli.style("IMPORTANT: ", fg="red"), nl=False)
        cli.out("TensorFlow does not appear to be installed.")
        _try_install_tensorflow(args)

def _try_load_tensorflow():
    log.debug("importing tensorflow")
    try:
        import tensorflow
    except ImportError as e:
        log.debug("error importing tensorflow: %s", e)
        return None
    else:
        log.debug("imported tensorflow")
        return tensorflow

def _try_install_tensorflow(args):
    if _gpu_available():
        pkg = "tensorflow-gpu"
    else:
        pkg = "tensorflow"
    prompt = "Would you like to install the %s package now?\n" % pkg
    if args.yes or cli.confirm(prompt, default=True):
        _install_tensorflow(pkg)

def _gpu_available():
    # Implementing this here initially. If it becomes generally
    # useful, move to `guild.gpu_util` or sim.
    import ctypes
    if "linux" in sys.platform:
        lib = "libcublas.so"
    elif sys.platform == "darwin":
        lib = "libcublas.dylib"
    elif sys.platform == "win32":
        lib = "cublas.dll"
    else:
        log.warning("unable to detect GPU for platform '%s'", sys.platform)
        lib = None
    if lib:
        log.debug("checking for GPU by loading %s", lib)
        try:
            ctypes.CDLL(lib)
        except OSError as e:
            log.debug("error loading '%s': %s", lib, e)
        else:
            log.debug("%s loaded", lib)
            return True
    return False

def _install_tensorflow(pkg):
    pip_util.install([pkg])

def _check_guild():
    check.check({})
