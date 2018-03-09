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

import guild

from guild import cli
from guild import cmd_impl_support
from guild import init
from guild import pip_util

from guild.commands.main import DEFAULT_GUILD_HOME

log = logging.getLogger("guild")

def main(args, ctx):
    if args.list_templates:
        _list_templates()
        return
    if args.help_template:
        _help_template(args.help_template)
        return
    _maybe_shift_first_param(args)
    if args.project_artifact == "project":
        _init_project(args, ctx)
    elif args.project_artifact == "model":
        _init_model(args, ctx)
    elif args.project_artifact == "package":
        _init_package(args, ctx)
    elif args.from_package:
        _init_project(args, ctx)
    else:
        assert args.project_artifact is None, args
        _init_env(args, ctx)

def _list_templates():
    print("##### list templates")

def _help_template(name):
    print("##### help template", name)

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
    template_path = os.path.join(
        guild.__pkgdir__,
        "guild",
        "templates",
        "projects",
        template)
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

def _init_model(args, ctx):
    cmd_impl_support.disallow_args(
        ["from_package", "local_resource_cache"],
        args, ctx, " with --model")
    print("###### init model:", args)

def _init_package(args, ctx):
    cmd_impl_support.disallow_args(
        ["params", "template", "from_package", "local_resource_cache"],
        args, ctx, " with --package")
    print("###### init package:", args)

def _init_env(args, ctx):
    cmd_impl_support.disallow_args(
        ["params", "template", "from_package"],
        args, ctx, " when initializing an environment")
    env_path = os.path.abspath(args.dir or os.path.dirname(DEFAULT_GUILD_HOME))
    cli.out("Initialzing Guild environment in %s" % env_path)
    init.init_env(env_path, args.local_resource_cache)
    if not args.skip_checks:
        _check_env(args, ctx)

def _check_env(args, ctx):
    _check_tensorflow(args, ctx)

def _check_tensorflow(args, ctx):
    tf = _try_load_tensorflow()
    if tf:
        cli.out("TensorFlow version %s installed" % tf.__version__)
    else:
        cli.out(cli.style("IMPORTANT: ", fg="red"), nl=False)
        cli.out("TensorFlow does not appear to be installed.")
        _try_install_tensorflow(args, ctx)

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

def _try_install_tensorflow(args, ctx):
    if _gpu_available():
        pkg = "tensorflow-gpu"
    else:
        pkg = "tensorflow"
    prompt = "Would you like to nstall the %s package now?\n" % pkg
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
            pass
        else:
            log.debug("%s loaded", lib)
            return True
    return False

def _install_tensorflow(pkg):
    pip_util.install([pkg])
