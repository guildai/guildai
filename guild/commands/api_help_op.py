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
    """Shows help info for an operation.

    `OPSPEC` is either a model operation for the current project or
    the path to Guild executable file.
    """
    api_support.out(_op_data(args), args)


def _op_data(args):
    import os
    from guild import flag_util
    from .run_impl import opdef_for_opspec

    opdef = opdef_for_opspec(args.opspec)
    return {
        "opref": _opref_data(opdef.opref),
        "name": opdef.name,
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
        "pkg_type": opref.pkg_type,
        "pkg_name": opref.pkg_name,
        "pkg_version": opref.pkg_version,
        "model_name": opref.model_name,
        "op_name": opref.op_name,
    }


def _flag_choices_data(choices):
    if not choices:
        return choices
    return [
        {
            "value": c.value,
            "alias": c.alias,
            "description": c.description,
        }
        for c in choices
    ]
