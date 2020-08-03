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

import json
import logging
import os
import platform
import re
import subprocess
import sys
import warnings

import click
import pkg_resources

import guild

from guild import _test
from guild import cli
from guild import config
from guild import file_util
from guild import plugin
from guild import uat
from guild import util
from guild import var

from . import remote_impl_support

log = logging.getLogger("guild")

CHECK_MODS = [
    "click",
    "distutils",
    "pip",
    "setuptools",
    "twine",
    "yaml",
    "werkzeug",
]


class Check(object):
    def __init__(self, args):
        self.args = args
        self._errors = False
        self.offline = self._init_offline(args)
        self.newer_version_available = False

    @staticmethod
    def _init_offline(args):
        if args.offline is not None:
            return args.offline
        else:
            return _check_config().get("offline")

    def error(self):
        self._errors = True

    @property
    def has_error(self):
        return self._errors


def _check_config():
    return config.user_config().get("check") or {}


def main(args):
    if args.remote:
        remote_impl_support.check(args)
    else:
        _check(args)


def _check(args):
    try:
        _check_impl(args)
    except SystemExit as e:
        _maybe_notify(args, e)
        raise
    else:
        _maybe_notify(args)


def _check_impl(args):
    if args.version:
        _check_version(args.version)
    if args.uat:
        _uat_and_exit()
    check = Check(args)
    if not args.no_info:
        _print_info(check)
    if args.all_tests or args.tests:
        _run_tests(check)
    if check.has_error:
        _print_error_and_exit(args)


def _check_version(req):
    try:
        match = guild.test_version(req)
    except ValueError:
        cli.error(
            "invalid requirement spec '%s'\n"
            "See https://bit.ly/guild-help-req-spec for more information." % req
        )
    else:
        if not match:
            cli.error(
                "version mismatch: current version '%s' does not match '%s'"
                % (guild.__version__, req)
            )


def _uat_and_exit():
    os.environ["NO_IMPORT_FLAGS_PROGRESS"] = "1"
    uat.run()
    sys.exit(0)


def _run_tests(check):
    os.environ["NO_IMPORT_FLAGS_PROGRESS"] = "1"
    os.environ["COLUMNS"] = "999"
    cli.MAX_WIDTH = 999
    if check.args.all_tests:
        if check.args.tests:
            log.warning(
                "running all tests (--all-tests specified) - "
                "ignoring individual tests"
            )
        success = _test.run_all(skip=check.args.skip)
    elif check.args.tests:
        if check.args.skip:
            log.warning("running individual tests - ignoring --skip")
        success = _test.run(check.args.tests)
    if not success:
        check.error()


def _print_info(check):
    _print_guild_info()
    _print_python_info(check)
    _print_platform_info()
    _print_psutil_info(check)
    _print_tensorboard_info(check)
    if check.args.tensorflow:
        _print_tensorflow_info(check)
    _print_cuda_info()
    _print_nvidia_tools_info()
    if check.args.verbose:
        _print_mods_info(check)
    _print_guild_latest_versions(check)
    if check.newer_version_available:
        _notify_newer_version()
    if check.args.space:
        _print_space()


def _print_guild_info():
    cli.out("guild_version:             %s" % guild.version())
    cli.out("guild_install_location:    %s" % _guild_install_location())
    cli.out("guild_home:                %s" % config.guild_home())
    cli.out("guild_resource_cache:      %s" % _guild_resource_cache())
    cli.out("installed_plugins:         %s" % _format_plugins())


def _guild_install_location():
    return pkg_resources.resource_filename("guild", "")


def _guild_resource_cache():
    return util.realpath(var.cache_dir("resources"))


def _format_plugins():
    return ", ".join([name for name, _ in sorted(plugin.iter_plugins())])


def _print_python_info(check):
    cli.out("python_version:            %s" % _python_version())
    cli.out("python_exe:                %s" % sys.executable)
    if check.args.verbose:
        cli.out("python_path:           %s" % _python_path())


def _python_version():
    return sys.version.replace("\n", "")


def _python_path():
    return os.path.pathsep.join(sys.path)


def _print_platform_info():
    cli.out("platform:                  %s" % _platform())


def _platform():
    system, _node, release, _ver, machine, _proc = platform.uname()
    return " ".join([system, release, machine])


def _print_psutil_info(check):
    ver = _try_module_version("psutil", check)
    _print_module_ver("psutil", ver)


def _print_tensorboard_info(check):
    try:
        import tensorboard.version as version
    except ImportError as e:
        check.error()
        cli.out("tensorboard_version:       %s" % _warn("not installed"))
        if check.args.verbose:
            cli.out("                           %s" % _warn(str(e)))
    else:
        cli.out("tensorboard_version:       %s" % version.VERSION)


def _print_tensorflow_info(check):
    # Run externally to avoid tf logging to our stderr
    cmd = [sys.executable, "-um", "guild.commands.tensorflow_check_main"]
    env = util.safe_osenv()
    env["PYTHONPATH"] = os.path.pathsep.join(sys.path)
    if check.args.verbose:
        stderr = None
    else:
        stderr = open(os.devnull, "w")
    p = subprocess.Popen(cmd, stderr=stderr, env=env)
    exit_status = p.wait()
    if exit_status != 0:
        check.error()


def _print_cuda_info():
    cli.out("cuda_version:              %s" % _cuda_version())


def _cuda_version():
    nvcc = util.which("nvcc")
    if not nvcc:
        return "not installed"
    try:
        out = subprocess.check_output([nvcc, "--version"])
    except subprocess.CalledProcessError as e:
        return _warn("ERROR: %s" % e.output.strip())
    else:
        out = out.decode("utf-8")
        m = re.search(r"V([0-9\.]+)", out, re.MULTILINE)
        if m:
            return m.group(1)
        else:
            log.debug("Unexpected output from nvidia-smi: %s", out)
            return "unknown (error)"


def _print_nvidia_tools_info():
    cli.out("nvidia_smi_version:        %s" % _nvidia_smi_version())


def _nvidia_smi_version():
    cmd = util.which("nvidia-smi")
    if not cmd:
        return "not installed"
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        return _warn("ERROR: %s" % e.output.strip())
    else:
        out = out.decode("utf-8")
        m = re.search(r"NVIDIA-SMI ([0-9\.]+)", out)
        if m:
            return m.group(1)
        else:
            log.debug("Unexpected output from nvidia-smi: %s", out)
            return "unknown (error)"


def _print_mods_info(check):
    for mod in CHECK_MODS:
        ver = _try_module_version(mod, check)
        _print_module_ver(mod, ver)


def _try_module_version(name, check, version_attr="__version__"):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            mod = __import__(name)
    except ImportError as e:
        check.error()
        return _warn("not installed (%s)" % e)
    else:
        try:
            ver = getattr(mod, version_attr)
        except AttributeError:
            return _warn("UNKNOWN")
        else:
            return _format_version(ver)


def _format_version(ver):
    if isinstance(ver, tuple):
        return ".".join([str(part) for part in ver])
    else:
        return str(ver)


def _print_module_ver(mod, ver):
    space = " " * (18 - len(mod))
    cli.out("%s_version:%s%s" % (mod, space, ver))


def _print_guild_latest_versions(check):
    if check.offline:
        cli.out("latest_guild_version:      unchecked (offline)")
    else:
        cur_ver = guild.__version__
        latest_ver = _latest_version(check)
        latest_ver_desc = latest_ver or "unknown (error)"
        cli.out("latest_guild_version:      %s" % latest_ver_desc)
        if latest_ver:
            check.newer_version_available = _is_newer(latest_ver, cur_ver)


def _latest_version(check):
    url = _latest_version_url(check)
    log.debug("getting latest version from %s", url)
    data = {
        "guild-version": guild.__version__,
        "python-version": _python_short_version(),
        "platform": _platform(),
    }
    try:
        resp = util.http_post(url, data, timeout=5)
    except Exception as e:
        log.debug("error reading latest version: %s", e)
        return None
    else:
        if resp.status_code == 404:
            log.debug("error reading latest version: %s not found" % url)
            return None
        if resp.status_code != 200:
            log.debug("error reading latest version: %s" % resp.text)
            return None
        return _parse_latest_version(resp.text)


def _latest_version_url(check):
    return _check_config().get("check-url") or check.args.check_url


def _python_short_version():
    return sys.version.split(" ", 1)[0]


def _parse_latest_version(s):
    try:
        decoded = json.loads(s)
    except Exception as e:
        log.debug("error parsing latest version response %s: %s", s, e)
        return None
    else:
        return decoded.get("latest-version", "unknown")


def _is_newer(latest, cur):
    return pkg_resources.parse_version(latest) > pkg_resources.parse_version(cur)


def _notify_newer_version():
    cli.out(
        click.style(
            "A newer version of Guild AI is available. Run "
            "'pip install guildai --upgrade' to install it.",
            bold=True,
        ),
        err=True,
    )


def _print_space():
    cli.out("disk_space:")
    _print_disk_usage("guild_home", config.guild_home())
    _print_disk_usage("runs", var.runs_dir())
    _print_disk_usage("deleted_runs", var.runs_dir(deleted=True))
    _print_disk_usage("remote_state", var.remote_dir())
    _print_disk_usage("cache", var.cache_dir())


def _print_disk_usage(name, path):
    if os.path.exists(path):
        size = file_util.disk_usage(path)
    else:
        size = 0
    ws = " " * max(1, 24 - len(name))
    cli.out("  %s:%s%s in %s" % (name, ws, util.format_bytes(size), path))


def _print_error_and_exit(args):
    if args.all_tests or args.tests:
        msg = _tests_failed_msg()
    else:
        msg = _general_error_msg(args)
    cli.error(msg)


def _tests_failed_msg():
    return "one or more tests failed - see above for details"


def _general_error_msg(args):
    msg = (
        "there are problems with your setup\n"
        "Refer to the issues above for more information"
    )
    if not args.verbose:
        msg += " or rerun check with the --verbose option."
    return msg


def _warn(msg):
    return click.style(msg, fg="red", bold=True)


def _maybe_notify(args, error=None):
    if not args.notify:
        return
    notify_send = util.which("notify-send")
    if not notify_send:
        log.warning("cannot notify check result - notify-send not available")
        return
    summary, body, urgency = _notify_cmd_params(error)
    cmd = ["notify-send", "-u", urgency, summary, body]
    _ = subprocess.check_output(cmd)


def _notify_cmd_params(error):
    from guild import main

    summary = "guild check"
    body = "PASSED"
    urgency = "normal"
    if error:
        error_msg, code = main.system_exit_params(error)
        # SystemExit errors are used for 0 exit codes, which are not
        # actually errors.
        if code != 0:
            body = "FAILED (%s)" % code
            if error_msg:
                body += ": %s" % error_msg
                urgency = "critical"
    return summary, body, urgency
