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

from . import ac_support


def _ac_file(_ctx, _param, incomplete):
    return ["-"] + ac_support.ac_filename(None, incomplete)


@click.command(hidden=True)
@click.option("-f", "--file", default="-", shell_complete=_ac_file)
@click_util.use_args
def schema(args):
    """Generate the current Guild file schema."""
    from guild import guildfile_schema

    out = guildfile_schema.schema_json()
    if args.file == "-":
        print(out)
    else:
        with open(args.file, "w") as f:
            f.write(out)
