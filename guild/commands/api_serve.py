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

from . import server_support


@click.command("serve")
@server_support.host_and_port_options
@click.option("--get", help="Perform a GET call and exit.")
@click_util.use_args
@click_util.render_doc
def main(args):
    """Start Guild API server.

    IMPORTANT: This command is experimental and subject to change without
    notice.
    """
    from .api_serve_impl import main
    main(args)
