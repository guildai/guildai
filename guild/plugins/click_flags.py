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

from __future__ import absolute_import
from __future__ import division

import argparse
import json
import logging
import os
import subprocess
import sys

import click

from guild import python_util
from guild import util

from . import import_argparse_flags_main
from . import python_script


def _init_log():
    # pylint: disable=invalid-envvar-default
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    logging.basicConfig(level=level, format=format)
    return logging.getLogger("import_flags_main")


log = _init_log()


class ClickFlags(python_script.PythonFlagsImporter):
    def flags_for_script(self, script, base_args):
        env = dict(os.environ)
        env.update(
            {
                "PYTHONPATH": os.path.pathsep.join([script.sys_path or ''] + sys.path),
                "LOG_LEVEL": str(log.getEffectiveLevel()),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        with util.TempFile() as tmp:
            cmd = [
                sys.executable,
                "-m",
                "guild.plugins.click_flags",
                script.src,
                script.mod_package or '',
                util.shlex_join(base_args),
                tmp.path,
            ]
            log.debug("click_flags env: %s", env)
            log.debug("click_flags cmd: %s", cmd)
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
            except subprocess.CalledProcessError as e:
                log.warning(
                    "cannot import flags from %s: %s",
                    os.path.relpath(script.src),
                    e.output.decode().strip(),
                )
                raise python_script.DataLoadError()
            else:
                out = out.decode()
                log.debug("click_flags output: %s", out)
                python_script._log_warnings(out, log)
                return python_script._load_data(tmp.path)


def main():
    args = _init_args()
    base_args = util.shlex_split(args.base_args)
    _patch_click(base_args, args.output_path)
    # Importing module has the side-effect of writing flag data due to
    # patched argparse.
    import_argparse_flags_main._exec_module(args.mod_path, args.package, base_args)


def _patch_click(base_args, output_path):
    handle_command_call = lambda group_call, *_args, **_kw: _write_command_flags(
        group_call, base_args, output_path
    )
    python_util.listen_method(click.Command, "__call__", handle_command_call)


def _write_command_flags(group_call_f0, base_args, output_path):
    called_cmd = _cmd_for_call_f(group_call_f0)
    op_cmd = _cmd_for_base_args(base_args, called_cmd)
    _write_flags(op_cmd.params, output_path)


def _cmd_for_call_f(call_f):
    closure = call_f.__closure__
    if len(closure) != 2:
        raise SystemExit("unexpected closure len for %s: %s" % (call_f, closure))
    cmd = closure[1].cell_contents
    if not isinstance(cmd, click.Command):
        raise SystemExit(
            "unexpected entry for group in closure for %s: %s" % (call_f, cmd)
        )
    return cmd


def _cmd_for_base_args(base_args, group):
    cmd = group
    for arg in base_args:
        try:
            cmd = cmd.commands[arg]
        except KeyError:
            break
    return cmd


def _write_flags(params, output_path):
    flags = _flags_for_click_params(params)
    log.debug("writing flags to %s: %s", output_path, flags)
    with open(output_path, "w") as f:
        json.dump(flags, f)


def _flags_for_click_params(params):
    flags = {}
    for param in params:
        _maybe_apply_flag(param, flags)
    return flags


def _maybe_apply_flag(param, flags):
    arg_name = _param_arg_name(param)
    if not arg_name or not isinstance(param, click.Option):
        log.debug("skipping %s - not a flag option", param.name)
        return
    flag_name = arg_name  # Use long form arg name as flag name.
    flags[flag_name] = attrs = {}
    if param.help:
        attrs["description"] = param.help
    if param.default is not None:
        attrs["default"] = _ensure_json_encodable(param.default, flag_name)
    if isinstance(param.type, click.Choice):
        attrs["choices"] = _ensure_json_encodable(param.type.choices, flag_name)
    if param.required:
        attrs["required"] = True
    if param.is_flag:
        attrs["arg-switch"] = not param.default
    log.debug("added flag %r: %r", flag_name, attrs)


def _ensure_json_encodable(val, name):
    return import_argparse_flags_main._ensure_json_encodable(val, name)


def _param_arg_name(param):
    for opt in param.opts:
        if opt.startswith("--"):
            return opt[2:]
    return None


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("mod_path")
    p.add_argument("package")
    p.add_argument("base_args")
    p.add_argument("output_path")
    return p.parse_args()


if __name__ == "__main__":
    main()
