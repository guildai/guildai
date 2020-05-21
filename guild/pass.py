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

"""No-op module that can be used for operation main.

This is useful during development or to simply print a message.
"""

from __future__ import print_function

import sys


if __name__ == "__main__":
    to_print = sys.argv[1:]
    if to_print:
        from guild import util

        print(*[util.shlex_quote(x) for x in to_print])
