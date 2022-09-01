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

import re

from guild import yaml_util

def runs_filter(expr):
    # TODO!

    if expr == "*":
        return lambda run: run
    return lambda run: _filter(run, expr)


def _filter(run, pattern):
    m = re.match(r"(.+?)=(.+)", pattern)
    if not m:
        return False
    flag_name, flag_val_str = m.groups()
    flag_val = yaml_util.decode_yaml(flag_val_str)
    actual_val = run.get("flags", {}).get(flag_name)
    return actual_val == flag_val
