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

import logging
import os

import six
import yaml

import guild.serve

from guild import cli
from guild import util

from guild.commands import runs_impl

log = logging.getLogger("guild")

def main(args, ctx):
    if args.model:
        _handle_path(args.model, args)
    else:
        _handle_run(runs_impl.one_run(args, ctx), args)

def _handle_path(path, args):
    if args.print_api:
        _print_api(path, args)
    elif args.print_model_info:
        _print_model_info(path)
    else:
        _serve_model(path, args)

def _handle_run(run, args):
    saved_models = _find_saved_models(run.path)
    if not saved_models:
        cli.out("Run %s does not contain any saved models" % run.id, err=True)
        cli.error()
    return _handle_path(_one_saved_model(saved_models), args)

def _find_saved_models(path):
    # pylint: disable=no-name-in-module
    from tensorflow.python.saved_model import loader # expensive
    paths = []
    for root, dirs, _files in os.walk(path):
        if loader.maybe_saved_model_directory(root):
            paths.append(root)
        util.try_remove(dirs, [".guild"])
    return paths

def _one_saved_model(paths):
    assert paths
    return sorted(paths)[-1]

class InfoDumper(yaml.SafeDumper):

    primitive_types = (
        float,
        six.integer_types,
        six.string_types
    )

    def __init__(self, *args, **kw):
        kw["default_flow_style"] = False
        super(InfoDumper, self).__init__(*args, **kw)

    def represent_sequence(self, tag, sequence, flow_style=None):
        base = super(InfoDumper, self).represent_sequence
        if sequence and isinstance(sequence[0], self.primitive_types):
            return base(tag, sequence, flow_style=True)
        return base(tag, sequence, flow_style)

def _print_api(path, args):
    info = guild.serve.model_api_info(path, _tags(args))
    formatted = yaml.dump(info, Dumper=InfoDumper)
    cli.out(formatted.strip())

def _tags(args):
    return [s.strip() for s in args.tags.split(",")]

def _print_model_info(path):
    info = guild.serve.model_info(path)
    formatted = yaml.dump(info, Dumper=InfoDumper)
    cli.out(formatted.strip())

def _serve_model(path, args):
    host = args.host or ""
    port = args.port or util.free_port()
    try:
        guild.serve.serve_forever(path, _tags(args), host, port)
    except IOError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("serving %s", path)
        cli.error(str(e))
