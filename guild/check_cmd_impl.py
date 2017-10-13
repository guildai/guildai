import logging
import os
import subprocess
import sys

import click

import guild.app
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

def main(args):
    if not args.no_info:
        _print_info(args)
    if args.all_tests or args.tests:
        _run_tests(args)

def _run_tests(args):
    if args.all_tests:
        if args.tests:
            logging.warn(
                "running all tests (--all-tests specified) - "
                "ignoring individual tests")
        success = guild.test.run_all(skip=args.skip)
    elif args.tests:
        if args.skip:
            logging.warn(
                "running individual tests - ignoring --skip")
        success = guild.test.run(args.tests)
    if not success:
        guild.cli.error()

def _print_info(args):
    _print_guild_info()
    _print_python_info(args.verbose)
    _print_tensorflow_info(args.verbose)
    _print_nvidia_tools_info()
    _print_mods_info()

def _print_guild_info():
    guild.cli.out("guild_version:             %s" % guild.app.version())
    guild.cli.out("guild_home:                %s" % guild.app.home())
    guild.cli.out("installed_plugins:         %s" % _format_plugins())

def _format_plugins():
    return ", ".join([name for name, _ in guild.plugin.iter_plugins()])

def _print_python_info(verbose):
    guild.cli.out("python_version:            %s" % _python_version())
    if verbose:
        guild.cli.out("python_path:           %s" % _python_path())

def _python_version():
    return sys.version.replace("\n", "")

def _python_path():
    return os.path.pathsep.join(sys.path)

def _print_tensorflow_info(verbose):
    # Run externally to avoid tf logging to our stderr
    _print_check_results("tensorflow-check", verbose)

def _print_nvidia_tools_info():
    _print_check_results("nvidia-tools-check")

def _print_check_results(script_name, verbose=False):
    script_path = guild.app.script(script_name)
    stderr = None if verbose else open(os.devnull, "w")
    out = subprocess.check_output(script_path, stderr=stderr)
    sys.stdout.write(out.decode(sys.stdout.encoding or "UTF-8"))

def _print_mods_info():
    for mod in CHECK_MODS:
        ver = _try_module_version(mod)
        space = " " * (18 - len(mod))
        guild.cli.out("%s_version:%s%s" % (mod, space, ver))

def _try_module_version(name):
    try:
        mod = __import__(name)
    except ImportError:
        return _warn("NOT INSTALLED")

    else:
        try:
            return mod.__version__
        except AttributeError:
            return _warn("UNKNOWN")

def _warn(msg):
    return click.style(msg, fg="red", bold=True)
