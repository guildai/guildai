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

import os

from guild import cli
from guild import util

from guild.commands import runs_impl

def main(args, ctx):
    if args.model:
        _serve_path(args.model)
    else:
        _serve_run(runs_impl.one_run(args, ctx))

def _serve_path(path):
    print("TODO: serve it!", path)

def _serve_run(run):
    saved_models = _find_saved_models(run.path)
    if not saved_models:
        cli.out("Run %s does not contain any saved models" % run.id, err=True)
        cli.error()
    return _serve_path(_one_saved_model(saved_models))

def _find_saved_models(path):
    paths = []
    for root, dirs, files in os.walk(path):
        if "saved_model.pb" in files:
            paths.append(root)
        util.try_remove(dirs, [".guild"])
    return paths

def _one_saved_model(paths):
    assert paths
    return sorted(paths)[-1]
