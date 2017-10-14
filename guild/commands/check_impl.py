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

import logging
import os
import subprocess
import sys

import click
import pkg_resources

import guild
import guild.cli
import guild.test

CHECK_MODS = [
    "pip",
    "psutil",
    "setuptools",
    "twine",
    "werkzeug",
    "yaml",
]

class Context(object):

    def __init__(self, args):
        self.args = args
        self._errors = False

    def error(self):
        self._errors = True

    @property
    def has_error(self):
        return self._errors

def main(args):
    ctx = Context(args)
    if not args.no_info:
        _print_info(ctx)
    if args.all_tests or args.tests:
        _run_tests(ctx)
    if ctx.has_error:
        guild.cli.error(
            "there are problems with your Guild setup\n"
            "Refer to the issues above for more information.")

def _run_tests(ctx):
    if ctx.args.all_tests:
        if ctx.args.tests:
            logging.warn(
                "running all tests (--all-tests specified) - "
                "ignoring individual tests")
        success = guild.test.run_all(skip=ctx.args.skip)
    elif ctx.args.tests:
        if ctx.args.skip:
            logging.warn(
                "running individual tests - ignoring --skip")
        success = guild.test.run(args.tests)
    if not success:
        ctx.error()

def _print_info(ctx):
    _print_guild_info()
    _print_python_info(ctx)
    _print_tensorflow_info(ctx)
    _print_nvidia_tools_info()
    _print_mods_info(ctx)

def _print_guild_info():
    guild.cli.out("guild_version:             %s" % guild.version())
    guild.cli.out("guild_home:                %s" % _guild_home())
    guild.cli.out("installed_plugins:         %s" % _format_plugins())

def _guild_home():
    return pkg_resources.resource_filename("guild", "")

def _format_plugins():
    return ", ".join([name for name, _ in guild.plugin.iter_plugins()])

def _print_python_info(ctx):
    guild.cli.out("python_version:            %s" % _python_version())
    if ctx.args.verbose:
        guild.cli.out("python_path:           %s" % _python_path())

def _python_version():
    return sys.version.replace("\n", "")

def _python_path():
    return os.path.pathsep.join(sys.path)

def _print_tensorflow_info(ctx):
    # Run externally to avoid tf logging to our stderr
    import guild.tensorflow_info_main
    cmd = [sys.executable, guild.tensorflow_info_main.__file__]
    env = {
        "PYTHONPATH": os.path.pathsep.join(sys.path)
    }
    env.update(guild.util.safe_osenv())
    stderr = None if ctx.args.verbose else open(os.devnull, "w")
    p = subprocess.Popen(cmd, stderr=stderr, env=env)
    exit_status = p.wait()
    if exit_status != 0:
        ctx.error()

def _print_nvidia_tools_info():
    guild.cli.out("nvidia_smi_available:      %s" % _nvidia_smi_available())

def _nvidia_smi_available():
    try:
        subprocess.check_output(["which", "nvidia-smi"])
    except (OSError, subprocess.CalledProcessError):
        return "no"
    else:
        return "yes"

def _print_mods_info(ctx):
    for mod in CHECK_MODS:
        ver = _try_module_version(mod, ctx)
        space = " " * (18 - len(mod))
        guild.cli.out("%s_version:%s%s" % (mod, space, ver))

def _try_module_version(name, ctx):
    try:
        mod = __import__(name)
    except ImportError:
        ctx.error()
        return _warn("NOT INSTALLED")
    else:
        try:
            return mod.__version__
        except AttributeError:
            return _warn("UNKNOWN")

def _warn(msg):
    return click.style(msg, fg="red", bold=True)
