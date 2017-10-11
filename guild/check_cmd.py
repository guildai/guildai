import os
import subprocess
import sys

import guild.app
import guild.cli
import guild.test

def main(args):
    if not args.no_info:
        _print_info(args.verbose)
    if args.all_tests or args.tests:
        _run_tests(args)

def _run_tests(args):
    if args.all_tests:
        if args.tests:
            sys.stdout.write(
                "Running all tests (--all-tests specified) - "
                "ignoring individual tests\n")
        success = guild.test.run_all()
    elif args.tests:
        success = guild.test.run(args.tests)
    if not success:
        guild.cli.error()

def _print_info(verbose):
    _print_guild_info()
    _print_python_info(verbose)
    _print_tensorflow_info(verbose)
    _print_nvidia_tools_info()
    _print_werkzeug_info()
    _print_psutil_info()
    _print_pyyaml_info()

def _print_guild_info():
    guild.cli.out("guild_version:             %s" % guild.app.version())
    guild.cli.out("guild_home:                %s" % guild.app.home())

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

def _print_werkzeug_info():
    ver = _try_module_version("werkzeug")
    guild.cli.out("werkzeug_version:          %s" % ver)

def _print_psutil_info():
    ver = _try_module_version("psutil")
    guild.cli.out("psutil_version:            %s" % ver)

def _print_pyyaml_info():
    ver = _try_module_version("yaml")
    guild.cli.out("pyyaml_version:            %s" % ver)

def _try_module_version(name):
    try:
        mod = __import__(name)
    except ImportError:
        return "NOT INSTALLED"
    else:
        return mod.__version__
