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

# (mod_name, required_flag)
CHECK_MODS = [
    ("click", True),
    ("distutils", True),
    ("numpy", True),
    ("pandas", False),
    ("pip", True),
    ("sklearn", True),
    ("skopt", True),
    ("setuptools", True),
    ("twine", False),
    ("yaml", True),
    ("werkzeug", True),
]

ATTR_COL_WIDTH = 26


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
    with util.Env(
        {
            "NO_IMPORT_FLAGS_PROGRESS": "1",
            "COLUMNS": "999",
            "SYNC_RUN_OUTPUT": "1",
        }
    ):
        _run_tests_(check)


def _run_tests_(check):
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
    _print_guild_info(check)
    _print_python_info(check)
    if not check.args.env:
        _print_platform_info(check)
        _print_psutil_info(check)
        _print_tensorboard_info(check)
        if check.args.tensorflow:
            _print_tensorflow_info(check)
        if check.args.pytorch:
            _print_pytorch_info(check)
        _print_cuda_info(check)
        _print_nvidia_tools_info(check)
        if check.args.verbose:
            _print_mods_info(check)
    _print_guild_latest_versions(check)
    if check.newer_version_available:
        _notify_newer_version()
    if not check.args.env:
        if check.args.space:
            _print_disk_usage()


def _print_guild_info(check):
    _attr("guild_version", _safe_apply(check, guild.version))
    _attr("guild_install_location", _safe_apply(check, _guild_install_location))
    _attr("guild_home", _safe_apply(check, config.guild_home))
    _attr("guild_resource_cache", _safe_apply(check, _guild_resource_cache))
    if not check.args.env:
        _attr("installed_plugins", _safe_apply(check, _format_plugins))


def _attr(name, val):
    cli.out("%s:%s%s" % (name, (ATTR_COL_WIDTH - len(name)) * " ", val))


def _safe_apply(check, f, *args, **kw):
    """Always return a string for application f(*args, **kw).

    If f(*args, **kw) fails, returns a higlighted error message and
    sets error flag on check.
    """
    try:
        return f(*args, **kw)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("safe call: %r %r %r", f, args, kw)
        check.error()
        return _warn("ERROR: %s" % e)


def _guild_install_location():
    return pkg_resources.resource_filename("guild", "")


def _guild_resource_cache():
    return util.realpath(var.cache_dir("resources"))


def _format_plugins():
    names = set([name for name, _ in plugin.iter_plugins()])
    return ", ".join(sorted(names))


def _print_python_info(check):
    _attr("python_version", _safe_apply(check, _python_version))
    _attr("python_exe", sys.executable)
    if check.args.verbose:
        _attr("python_path", _safe_apply(check, _python_path))


def _python_version():
    return sys.version.replace("\n", "")


def _python_path():
    return os.path.pathsep.join(sys.path)


def _print_platform_info(check):
    _attr("platform", _safe_apply(check, _platform))


def _platform():
    system, _node, release, _ver, machine, _proc = platform.uname()
    return " ".join([system, release, machine])


def _print_psutil_info(check):
    ver = _try_module_version("psutil", check)
    _attr("psutil_version", ver)


def _print_tensorboard_info(check):
    _attr("tensorboard_version", _safe_apply(check, _tensorboard_version, check))


def _tensorboard_version(check):
    try:
        import tensorboard.version as version
    except ImportError:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("tensorboard version")
        check.error()  # TB is required
        return _warn("not installed")
    else:
        return version.VERSION


def _print_tensorflow_info(check):
    # Run externally to avoid tf logging to our stderr.
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


def _print_pytorch_info(check):
    torch = _try_import_torch()
    if not torch:
        _attr("pytorch_version", _warn("not installed"))
        return
    _attr("pytorch_version", _safe_apply(check, _torch_version, torch))
    _attr("pytorch_cuda_version", _safe_apply(check, _torch_cuda_version, torch))
    _attr("pytorch_cuda_available", _safe_apply(check, _torch_cuda_available, torch))
    _attr("pytorch_cuda_devices", _safe_apply(check, _pytorch_cuda_devices, torch))


def _try_import_torch():
    # pylint: disable=import-error
    try:
        import torch
        import torch.version as _
    except Exception:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("try import torch")
        return None
    else:
        return torch


def _torch_version(torch):
    return torch.version.__version__


def _torch_cuda_version(torch):
    return torch.version.cuda


def _torch_cuda_available(torch):
    if torch.cuda.is_available():
        return "yes"
    else:
        return "no"


def _pytorch_cuda_devices(torch):
    if torch.cuda.device_count == 0:
        return "none"
    return ", ".join(
        "%s (%i)" % (torch.cuda.get_device_name(i), i)
        for i in range(torch.cuda.device_count())
    )


def _print_cuda_info(check):
    _attr("cuda_version", _safe_apply(check, _cuda_version))


def _cuda_version():
    version = util.find_apply([_cuda_version_nvcc, _cuda_version_nvidia_smi])
    if not version:
        return "not installed"
    return version


def _cuda_version_nvcc():
    nvcc = util.which("nvcc")
    if not nvcc:
        return None
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
            log.debug("Unexpected output from nvcc: %s", out)
            return "unknown (error)"


def _cuda_version_nvidia_smi():
    nvidia_smi = util.which("nvidia-smi")
    if not nvidia_smi:
        return None
    try:
        out = subprocess.check_output([nvidia_smi, "--query"])
    except subprocess.CalledProcessError as e:
        return _warn("ERROR: %s" % e.output.strip())
    else:
        out = out.decode("utf-8")
        m = re.search(r"CUDA Version\s+: ([0-9\.]+)", out, re.MULTILINE)
        if m:
            return m.group(1)
        else:
            log.debug("Unexpected output from nvidia-smi: %s", out)
            return "unknown (error)"


def _print_nvidia_tools_info(check):
    _attr("nvidia_smi_version", _safe_apply(check, _nvidia_smi_version))


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
    for mod, required in CHECK_MODS:
        ver = _try_module_version(mod, check, required)
        _attr("%s_version" % mod, ver)


def _try_module_version(name, check, required=True, version_attr="__version__"):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("ignore", RuntimeWarning)
            mod = __import__(name)
    except ImportError as e:
        if required:
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


def _print_guild_latest_versions(check):
    if check.offline:
        _attr("latest_guild_version", "unchecked (offline)")
    else:
        cur_ver = guild.__version__
        latest_ver = _latest_version(check)
        latest_ver_desc = latest_ver or "unknown (error)"
        _attr("latest_guild_version", latest_ver_desc)
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


def _print_disk_usage():
    cli.out("disk_space:")
    paths = [
        ("guild_home", config.guild_home()),
        ("runs", var.runs_dir()),
        ("deleted_runs", var.runs_dir(deleted=True)),
        ("remote_state", var.remote_dir()),
        ("cache", var.cache_dir()),
    ]
    formatted_disk_usage = [_formatted_disk_usage(path) for _name, path in paths]
    max_disk_usage_width = max([len(s) for s in formatted_disk_usage])
    for (name, path), disk_usage in zip(paths, formatted_disk_usage):
        _attr(
            "  %s" % name,
            _format_disk_usage_and_path(disk_usage, path, max_disk_usage_width),
        )


def _formatted_disk_usage(path):
    if os.path.exists(path):
        size = file_util.disk_usage(path)
    else:
        size = 0
    return util.format_bytes(size)


def _format_disk_usage_and_path(usage, path, max_usage_width):
    return "%s%s%s" % (usage, " " * (max_usage_width - len(usage) + 1), path)


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
