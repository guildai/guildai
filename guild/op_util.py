# Copyright 2017 TensorHub, Inc.
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

from guild import util

def resolve_file(filename):
    return util.find_apply([
        _abs_file,
        _cmd_file,
        _model_file,
        _cwd_file
    ], filename)

def _abs_file(filename):
    if os.path.isabs(filename):
        return filename

def _cmd_file(filename):
    assert "CMD_DIR" in os.environ
    filename = os.path.join(os.environ["CMD_DIR"], filename)
    if os.path.exists(filename):
        return filename

def _model_file(filename):
    assert "MODEL_DIR" in os.environ
    filename = os.path.join(os.environ["MODEL_DIR"], filename)
    if os.path.exists(filename):
        return filename

def _cwd_file(filename):
    return os.path.join(os.getcwd(), filename)
