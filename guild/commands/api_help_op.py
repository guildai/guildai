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

import click

from guild import click_util

from . import api_support
from . import run as run_cmd


@click.command("help-op")
@click.argument(
    "opspec",
    metavar="OPSPEC",
    shell_complete=run_cmd._ac_opspec,
)
@api_support.output_options
@click_util.use_args
@click_util.render_doc
def main(args):
    """Shows help info for an operation as JSON.

    IMPORTANT: This command is experimental and subject to change without
    notice.

    `OPSPEC` is either a model operation for the current project or
    the path to Guild executable file.
    """
    api_support.out(_op_data(args), args)


def _op_data(args):
    from .run_impl import opdef_for_opspec

    opdef = opdef_for_opspec(args.opspec)
    return op_info_for_opdef(opdef)


def op_info_for_opdef(opdef):
    from guild import flag_util

    return {
        "opref": _opref_data(opdef.opref),
        "name": opdef.name,
        "fullname": opdef.fullname,
        "description": opdef.description,
        "guildfile": {
            "dir": os.path.abspath(opdef.guildfile.dir),
            "src": opdef.guildfile.src,
        },
        "flags": {
            f.name: {
                "default": f.default,
                "defaultAssign": flag_util.flag_assign(f.name, f.default),
                "description": f.description,
                "choices": _flag_choices_data(f.choices),
                "type": f.type,
            }
            for f in opdef.flags
        },
    }


def _opref_data(opref):
    return {
        "pkgType": opref.pkg_type,
        "pkgName": opref.pkg_name,
        "pkgVersion": opref.pkg_version,
        "modelName": opref.model_name,
        "opName": opref.op_name,
    }


def _flag_choices_data(choices):
    if not choices:
        return choices
    return [
        {
            "value": c.value,
            "alias": c.alias,
            "description": c.description,
        } for c in choices
    ]
