# Copyright 2017-2023 Posit Software, PBC
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
import re
import subprocess

import yaml

import guild

from guild import cli
from guild import config
from guild import model as modellib
from guild import model_proxy
from guild import plugin as pluginlib
from guild import r_util

log = logging.getLogger("guild")


class RScriptBuiltinsModelProxy:
    def __init__(self):
        self.name = "r-script"
        self.reference = modellib.ModelRef(
            "builtin",
            "guildai",
            guild.__version__,
            self.name,
        )
        self.modeldef = model_proxy.modeldef(
            self.name,
            {
                "operations": {
                    "init": {
                        "description": "Initialize R script support for Guild.",
                        "main": "guild.plugins.r_script_init_main",
                    }
                }
            },
            f"<{self.__class__.__name__}>",
        )


class RScriptModelProxy:
    name = ""
    output_scalars = None
    objective = "loss"
    plugins = []

    def __init__(self, script_path, op_name):
        assert script_path[-2:].upper() == ".R", script_path
        assert script_path.endswith(op_name), (script_path, op_name)
        _ensure_guildai_r_package_installled()
        self.script_path = script_path
        if os.path.isabs(op_name) or op_name.startswith(".."):
            self.op_name = os.path.basename(op_name)
        else:
            self.op_name = op_name
        script_base = script_path[: -len(self.op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)
        self.modeldef = model_proxy.modeldef(
            self.name,
            {
                "operations": {
                    self.op_name: _op_data_for_script(script_path),
                }
            },
            dir=os.path.dirname(script_path),
        )
        _apply_config_flags(self.modeldef, self.op_name)


def _apply_config_flags(modeldef, op_name):
    from . import config_flags

    opdef = modeldef.get_operation(op_name)
    config_flags.apply_config_flags(opdef)


class RScriptPlugin(pluginlib.Plugin):
    resolve_model_op_priority = 60

    def resolve_model_op(self, opspec):
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to an R based operation, returns
        None.
        """
        if opspec == "r-script:init":
            return _r_script_init_model_op()
        return _maybe_r_script_model_op(opspec)

    def enabled_for_op(self, opdef):
        if r_util.is_r_script(opdef.name):
            return True, "operation is an R script"
        return False, "operation is not an R script"


def _r_script_init_model_op():
    return RScriptBuiltinsModelProxy(), "init"


def _maybe_r_script_model_op(opspec):
    path = _path_for_opspec(opspec)
    if not r_util.is_r_script(path):
        return None
    model = RScriptModelProxy(path, opspec)
    return model, model.op_name


def _path_for_opspec(opspec):
    if opspec.startswith(("/", "./")) and os.path.isfile(opspec):
        return opspec
    return os.path.join(config.cwd(), opspec)


def _op_data_for_script(r_script_path):
    try:
        out = run_r("guildai:::emit_r_script_guild_data()", args=[r_script_path])
    except subprocess.CalledProcessError as e:
        log.warning(e.output.rstrip().decode("utf-8"))
        return {}
    else:
        return yaml.safe_load(out)


def _ensure_guildai_r_package_installled(version="0.0.0.9001"):
    is_installed_expr = (
        'cat(requireNamespace("guildai", quietly = TRUE) &&'
        f' getNamespaceVersion("guildai") >= "{version}")'
    )

    installed = run_r(is_installed_expr) == "TRUE"
    if installed:
        return

    cli.error(
        "missing required 'guildai' R package\n"
        "Install it by running 'guild run r-script:init' and try again."
    )

    # TODO, consider vendoring r-pkg as part of pip pkg,
    # auto-bootstrap R install into a stand-alone lib we inject via
    # prefixing R_LIBS env var


class RscriptProcessError(Exception):
    def __init__(self, error_output, returncode):
        self.error_output = error_output
        self.returncode = returncode


def run_r(
    *exprs,
    file=None,
    infile=None,
    vanilla=True,
    args=None,
    default_packages='base',
    **run_kwargs,
):
    """Run R code in a subprocess, return stderr+stdout output in a single string.

    This has different defaults from `Rscript`, designed for isolated,
    fast invocations.

    Args:
      `exprs`: strings of individual R expressions to be evaluated sequentially
      `file`: path to an R script
      `infile`: multiline string of R code, piped into Rscript frontend via stdin.

    """
    assert (
        sum(map(bool, [exprs, file, infile])) == 1
    ), "exprs, file, and infile, are mutually exclusive. Only supply one."

    cmd = ["Rscript"]
    if default_packages:
        cmd.append(f"--default-packages={default_packages}")
    if vanilla:
        cmd.append("--vanilla")
    if file:
        cmd.append(file)
    elif exprs:
        for e in exprs:
            cmd.extend(["-e", e])
    elif infile:
        cmd.append("-")
        run_kwargs['input'] = infile.encode()

    if args:
        cmd.extend(args)

    run_kwargs.setdefault('capture_output', True)

    try:
        return subprocess.run(cmd, check=True, **run_kwargs).stdout.decode()
    except subprocess.CalledProcessError as e:
        raise RscriptProcessError(e.stderr.decode(), e.returncode) from None


def merge_dicts(dict1, dict2):
    """Recursively merges dict2 into dict1. Modifies dict1 in place"""
    for k in dict2:
        if k in dict1:
            dict1[k] = merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]
    return dict1


def r_script_version():
    out = subprocess.check_output(
        ["Rscript", "--version"],
        stderr=subprocess.STDOUT,
    ).decode()
    m = re.search(r"R scripting front-end version (.*)", out)
    if not m:
        raise ValueError(f"unknown version ({out})")
    return m.group(1)
