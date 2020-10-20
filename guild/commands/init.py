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

import click

from guild import click_util


def _ac_python(**_kw):
    return click_util.completion_command("python*[^-config]")


def _ac_guild_version_or_path(incomplete, ctx, **_kw):
    versions = [ver for ver in _guild_versions(ctx) if ver.startswith(incomplete)]
    return versions + click_util.completion_filename(ext=["whl"])


def _guild_versions(ctx):
    import json

    # We want to import pip._vendor.requests but pip has an import
    # cycle so we get to it via pip._internal.index.
    from pip._internal.index import requests

    def f():
        resp = requests.get("https://pypi.org/pypi/guildai/json")
        data = json.loads(resp.text)
        return sorted(data.get("releases") or {})

    return click_util.completion_safe_apply(ctx, f, []) or []


def _ac_guild_home(**_kw):
    return click_util.completion_dir()


def _ac_requirement(**_kw):
    return click_util.completion_filename(ext=["txt"])


def _ac_path(**_kw):
    return click_util.completion_dir()


@click.command()
@click.argument("dir", default="venv", autocompletion=click_util.completion_dir)
@click.option(
    "-n",
    "--name",
    metavar="NAME",
    help="Environment name (default is env parent directory name).",
)
@click.option(
    "-p",
    "--python",
    metavar="VERSION",
    help="Version of Python to use for the environment.",
    autocompletion=_ac_python,
)
@click.option(
    "-g",
    "--guild",
    metavar="VERSION_OR_PATH",
    help=(
        "Version of Guild AI to use for the environment. "
        "By default, the active version of Guild is installed. This "
        "value may alternatively be a path to a Guild wheel distribution."
    ),
    autocompletion=_ac_guild_version_or_path,
)
@click.option(
    "-s",
    "--system-site-packages",
    is_flag=True,
    help="Give environment access to system site packages.",
)
@click.option(
    "-H",
    "--no-isolate",
    is_flag=True,
    help=(
        "Use current Guild home for the environment. Ignored if `--guild-home` "
        "is also specified, this option is ignored."
    ),
)
@click.option(
    "-h",
    "--guild-home",
    metavar="PATH",
    help=(
        "Alternative Guild home location associated with the environment. "
        "By default, Guild home is '.guild' in the environment directory."
    ),
    autocompletion=_ac_guild_home,
)
@click.option(
    "-r",
    "--requirement",
    metavar="REQ",
    multiple=True,
    help=(
        "Install required package or packages defined in a file. May be "
        "used multiple times."
    ),
    autocompletion=_ac_requirement,
)
@click.option(
    "-P",
    "--path",
    metavar="DIR",
    multiple=True,
    help="Include DIR as a Python path in the environment.",
    autocompletion=_ac_path,
)
@click.option(
    "--no-reqs",
    is_flag=True,
    help=(
        "Don't install from requirements.txt or guild.yml in environment "
        "parent directory."
    ),
)
@click.option(
    "-l",
    "--isolate-resources",
    is_flag=True,
    help="Use a local cache when initializing an environment.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Initialize a Guild environment without prompting.",
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Don't show progress when installing environment packages.",
)
@click_util.use_args
def init(args):
    """Initialize a Guild environment.

    `init` initializes a Guild environment in `DIR`, which is the
    current directory by default.

    `init` creates a virtual environment in `DIR` using the `venv`
    module if available or the `virtualenv` program if `venv` is not
    available.

    Use `--python` to specify the Python interpreter to use within the
    generated virtual environment. By default, the default Python
    interpreter for `virtualenv` is used unless `python` is explicitly
    listed as a requirement. If `no-venv` is specified, `--python` is
    ignored.

    ### Requirements

    By default, any required packages listed under packages.requires
    in `guild.yml` in the environment parent directory are installed
    into the environment. Use `--no-reqs` to suppress this behavior.

    Additionally, packages defined in `requirements.txt` in the
    environment parent directory will be installed. Use `--no-reqs` to
    suppress this behavior.

    Note that packages defined in `guild.yml` use Guild package names
    while packages defined in `requirements.txt` use PyPI package
    names.

    For information on requirements files, see:

    https://bit.ly/guild-help-req-files

    You may explicitly specify requirements file using `-r` or
    `--requirement`. If `-r, --requirement` is specified, Guild will
    not automatically install packages in `requirements.txt` -- that
    file must be specified explicitly in the command.

    ### Guild AI Version

    By default `init` installs the active version of Guild AI in the
    initialized environment. To install a different version, or to
    install a Guild wheel distribution file use the `--guild` option.

    ### Resource Cache

    By default resources are cached and shared at the user level in
    `~/.guild/cache/resources` so that resources downloaded from one
    environment are available to other environments. You can modify
    this behavior to have all resources downloaded local to the
    environment by specifying `--local-resource-cache`.

    """
    from . import init_impl

    init_impl.main(args)
