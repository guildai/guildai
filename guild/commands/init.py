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

import click

from guild import click_util

from . import ac_support


def _ac_python(_ctx, _param, incomplete):
    return ac_support.ac_python(incomplete)


def _ac_guild_version_or_path(_ctx, _param, incomplete):
    versions = [ver for ver in _guild_versions() if ver.startswith(incomplete)]
    return versions + ac_support.ac_filename(["whl"], incomplete)


def _guild_versions():
    import json
    from urllib.request import urlopen

    def f():
        resp = urlopen("https://pypi.org/pypi/guildai/json")
        data = json.loads(resp.read())
        return sorted(data.get("releases") or {})

    return ac_support.ac_safe_apply(f, []) or []


def _ac_guild_home(_ctx, _param, incomplete):
    return ac_support.ac_dir(incomplete)


def _ac_requirement(_ctx, _param, incomplete):
    return ac_support.ac_filename(["txt"], incomplete)


def _ac_dir(_ctx, _param, incomplete):
    return ac_support.ac_dir(incomplete)


@click.command()
@click.argument("dir", default=None, required=False, shell_complete=_ac_dir)
@click.option(
    "--venv",
    is_flag=True,
    help=(
        "Creates a virtual environment in DIR. This option "
        "enabled pre-0.9 init behavior and is implied when "
        "specifying any of the virtual environment settings below."
    ),
)
@click.option(
    "-n",
    "--name",
    metavar="NAME",
    help=("Environment name (default is env parent directory name). Implies `--venv`."),
)
@click.option(
    "-p",
    "--python",
    metavar="VERSION",
    help=("Version of Python to use for the environment. Implies `--venv`."),
    shell_complete=_ac_python,
)
@click.option(
    "-g",
    "--guild",
    metavar="VERSION_OR_PATH",
    help=(
        "Version of Guild AI to use for the environment. The activate "
        "version of Guild is installed by default. This value may "
        "alternatively be a path to a Guild wheel distribution. Implies "
        "`--venv`."
    ),
    shell_complete=_ac_guild_version_or_path,
)
@click.option(
    "-s",
    "--system-site-packages",
    is_flag=True,
    help="Give environment access to system site packages. Implies `--venv`.",
)
@click.option(
    "-H",
    "--no-isolate",
    is_flag=True,
    help=(
        "Use current Guild home for the environment. Ignored if `--guild-home` "
        "is specified."
    ),
)
@click.option(
    "-h",
    "--guild-home",
    metavar="PATH",
    help=(
        "Alternative Guild home location for with the environment. "
        "By default, Guild home is '.guild' in `DIR`."
    ),
    shell_complete=_ac_guild_home,
)
@click.option(
    "-r",
    "--requirements",
    metavar="REQ",
    multiple=True,
    help=(
        "Install required package or packages defined in a file. May be "
        "used multiple times. Implies `--venv`."
    ),
    shell_complete=_ac_requirement,
)
@click.option(
    "-P",
    "--path",
    metavar="DIR",
    multiple=True,
    help="Include DIR as a Python path in the environment. Implies `--venv`.",
    shell_complete=_ac_dir,
)
@click.option(
    "--no-reqs",
    is_flag=True,
    help=(
        "Don't install from requirements.txt or guild.yml in environment "
        "parent directory. Implies `--venv`."
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
    help=(
        "Don't show progress when installing environment packages. Ignored "
        "if a virtual environment is not created."
    ),
)
@click.option(
    "--pre",
    "pre_release",
    is_flag=True,
    help="Install pre-release versions of applicable packages. Implies `--venv`.",
)
@click_util.use_args
def init(args):
    """Initialize a Guild environment.

    By default, creates `.guild` under `DIR`, or the current directory
    if `DIR` is omitted.

    NOTE: As of 0.9, this command does NOT create a virtual directory
    in `DIR`. To enable pre-0.9 behavior, specify `--venv` along with
    any of the applicable virtual environment options. We recommend
    creating a virtual environment using standard tools rather than
    using this command. Backward compatibility will be maintained via
    the `--venv` option.

    Options that are associated with virtual environments are noted as
    such below.

    ### Resource Cache

    By default resources are cached and shared at the user level in
    `~/.guild/cache/resources` so that resources downloaded from one
    environment are available to other environments. You can modify
    this behavior to have all resources downloaded local to the
    environment by specifying `--local-resource-cache`.

    ### Python Interpreter (virtual environments only)

    Use `--python` to specify the Python interpreter to use within the
    generated virtual environment. By default, the default Python
    interpreter for `virtualenv` is used unless `python` is explicitly
    listed as a requirement. If `no-venv` is specified, `--python` is
    ignored.

    ### Requirements (virtual environments only)

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

    ### Guild AI Version (virtual environments only)

    By default `init` installs the active version of Guild AI in the
    initialized environment. To install a different version, or to
    install a Guild wheel distribution file use the `--guild` option.
    """
    from . import init_impl

    init_impl.main(args)
