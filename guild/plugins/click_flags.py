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

import argparse
import json
import logging as logging
import os
import subprocess
import sys

import click

from guild import python_util
from guild import util

from . import import_argparse_flags_main
from . import python_script


def _init_log():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    logging.basicConfig(level=level, format=format)
    return logging.getLogger("import_flags_main")


log = _init_log()


class ClickFlags(python_script.PythonFlagsImporter):
    def flags_for_script(self, script, log):
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
                tmp.path,
            ]
            log.debug("click_flags env: %s", env)
            log.debug("click_flags cmd: %s", cmd)
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
            except subprocess.CalledProcessError as e:
                log.warning(
                    "cannot import flags from %s: %s",
                    script.src,
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
    _patch_click(args.output_path)
    # Importing module has the side-effect of writing flag data due to
    # patched argparse.
    import_argparse_flags_main._exec_module(args.mod_path, args.package)


def _patch_click(output_path):
    handle_cmd_init = lambda _init, *_args, **kw: _write_flags(
        kw["params"], output_path
    )
    python_util.listen_method(click.Command, "__init__", handle_cmd_init)


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
    flag_name = param.name
    flags[flag_name] = attrs = {}
    if arg_name != flag_name:
        attrs["arg-name"] = arg_name
    if param.help:
        attrs["description"] = param.help
    if param.default is not None:
        attrs["default"] = _ensure_json_encodable(param.default, flag_name)
    if isinstance(param.type, click.Choice):
        attrs["choices"] = _ensure_json_encodable(param.type.choices, flag_name)
    if param.required:
        attrs["required"] = True
    if param.is_flag:
        attrs["arg-switch"] = param.default
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
    p.add_argument("output_path")
    return p.parse_args()


if __name__ == "__main__":
    main()
