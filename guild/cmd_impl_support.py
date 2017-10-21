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

import logging
import os

import guild.model

from guild import cli
from guild import modelfile

def cwd(ctx):
    """Returns the cwd for a command context."""
    return ctx.obj["cwd"]

def cwd_desc(ctx):
    """Returns a description for the context cwd.

    If the context is the same as the system cwd, returns "this
    directory" otherwise returns the quoted cwd.

    This is used in messages to the user where the cwd is referenced.
    """
    cwd_ = cwd(ctx)
    if os.path.abspath(cwd_) == os.path.abspath(os.getcwd()):
        return "the current directory"
    else:
        return "'%s'" % cwd_

def cwd_modelfile(ctx):
    """Returns a modelfile for a context cwd or None if one doesn't exit."""
    cwd_ = cwd(ctx)
    for name in modelfile.NAMES:
        path = os.path.join(cwd_, name)
        if os.path.exists(path):
            return path
    return None

def cwd_modeldef(ctx):
    cwd_ = cwd(ctx)
    try:
        return modelfile.from_dir(cwd_)
    except (modelfile.NoModels, IOError):
        return None
    except Exception as e:
        logging.warning("unable to load modeldef from %s: %s", cwd_, e)
        return None

def init_model_path(ctx, force_all=False, notify_force_all_option=None):
    """Initializes the model path given a command context.

    If the context cwd contains a model def, the path is initialized
    so that only models associated with the cwd are available via
    `guild.model`. An exception to this is when `force_all` is true,
    in which case all models including those in the cwd will be
    available.
    """
    model_source = cwd_modelfile(ctx)
    if model_source:
        if force_all:
            guild.model.add_model_source(model_source)
        else:
            _maybe_notify_models_limited(notify_force_all_option, ctx)
            guild.model.set_path([model_source])

def _maybe_notify_models_limited(force_all_option, ctx):
    if force_all_option:
        cli.note(
            "Limiting models to %s (use %s to include all)."
            % (cwd_desc(ctx), force_all_option))
