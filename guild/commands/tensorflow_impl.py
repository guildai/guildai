# Copyright 2017-2018 TensorHub, Inc.
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

from guild import cli

def inspect_checkpoint(args):
    try:
        from tensorflow.python.tools import inspect_checkpoint as inspect
    except ImportError as e:
        _handle_import_error(e)
    else:
        inspect.FLAGS = args
        inspect.main([])

def _handle_import_error(e):
    if "tensorflow" in str(e):
        cli.out(
            "TensorFlow is not installed.\n"
            "Refer to https://www.tensorflow.org/install/ for help "
            "installing TensorFlow on your system.", err=True)
    else:
        cli.out("Error loading TensorBoard: %s" % e, err=True)
    cli.error()
