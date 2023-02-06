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

from .api_compare import main as compare
from .api_help_op import main as help_op
from .api_merge import main as merge
from .api_ops import main as ops
from .api_runs import main as runs


@click.group(cls=click_util.Group)
def api(**_kw):
    """CLI based API calls.

    IMPORTANT: These commands are experimental and subject to change without
    notice.
    """


api.add_command(compare)
api.add_command(help_op)
api.add_command(merge)
api.add_command(ops)
api.add_command(runs)
