# Copyright 2017-2019 TensorHub, Inc.
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
from . import runs_import

@click.command("import")
@runs_import.import_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def import_(ctx, args):
    """{{ runs_import.import_runs }}"""

    from . import runs_impl
    runs_impl.import_(args, ctx)
