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

from __future__ import absolute_import
from __future__ import division

import os

import guild.cli
import guild.cmd_support
import guild.project

DEFAULT_PROJECT_LOCATION = "."

def main(args, ctx):
    project = guild.cmd_support.project_for_location(
        args.project_location, ctx)
    guild.cli.table(
        [_format_op(op) for op in _iter_ops(project, args)],
        cols=["full_name", "description"],
        detail=(["cmd"] if args.verbose else []))

def _iter_ops(project, args):
    for model in _project_models(project, args):
        for op in model.operations:
            yield op

def _project_models(project, args):
    if args.model:
        return [_try_model(args.model, project)]
    else:
        return list(project)

def _try_model(name, project):
    try:
        return project[name]
    except KeyError:
        _no_such_model_error(name, project)

def _no_such_model_error(name, project):
    guild.cli.error(
        "model '%s' is not defined in %s\n"
        "Try 'guild models%s' for a list of models."
        % (name, os.path.relpath(project.src),
           _project_opt(project.src)))

def _project_opt(project_src):
    relpath = os.path.relpath(project_src)
    if relpath == "MODEL" or relpath == "MODELS":
        return ""
    else:
        return " -p %s" % relpath

def _format_op(op):
    return {
        "name": op.name,
        "model": op.model.name,
        "full_name": "%s:%s" % (op.model.name, op.name),
        "description": op.description or "",
        "cmd": op.cmd,
    }
