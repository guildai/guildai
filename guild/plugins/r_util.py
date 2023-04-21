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

import os
import re
import subprocess

from guild import util


class REnvError(Exception):
    pass


class RScriptProcessError(Exception):
    def __init__(self, error_output, returncode):
        self.error_output = error_output
        self.returncode = returncode


def is_r_script(opspec):
    return os.path.isfile(opspec) and opspec[-2:].upper() == ".R"


def verify_r_env():
    _verify_r()
    _verify_r_package()


def _verify_r():
    if not util.which("Rscript"):
        raise REnvError(
            "R is not installed on this system. Refer to "
            "https://www.r-project.org/ for details."
        )


def _verify_r_package(min_version="0.0.0.9001"):
    installed_version = r_package_version()
    if not installed_version:
        raise REnvError(
            "R package 'guildai' is not installed\n"
            "Install it by running 'guild run r-script:init' and try again."
        )
    if installed_version < min_version:
        raise REnvError(
            f"R package 'guildai' is too old (got version '{installed_version})'\n"
            "Upgrade the package by running 'guild run r-script:init' and try again."
        )


def r_package_version():
    return run_r(
        "cat(if(requireNamespace(\"guildai\")) "
        "getNamespaceVersion(\"guildai\") else \"\")"
    )


def run_r(
    *exprs,
    file=None,
    infile=None,
    vanilla=True,
    args=None,
    default_packages="base",
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
    _check_run_args(exprs, file, infile)
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
        run_kwargs["input"] = infile.encode()

    if args:
        cmd.extend(args)

    run_kwargs.setdefault("capture_output", True)

    try:
        return subprocess.run(cmd, check=True, **run_kwargs).stdout.decode()
    except subprocess.CalledProcessError as e:
        raise RScriptProcessError(e.stderr.decode(), e.returncode) from None


def _check_run_args(exprs, file, infile):
    if sum(map(bool, [exprs, file, infile])) != 1:
        raise TypeError(
            "exprs, file, and infile, are mutually exclusive - only supply one"
        )


def r_script_version():
    out = subprocess.check_output(
        ["Rscript", "--version"],
        stderr=subprocess.STDOUT,
    ).decode()
    m = re.search(r"R scripting front-end version (.*)", out)
    if not m:
        raise ValueError(f"unknown version ({out})")
    return m.group(1)
