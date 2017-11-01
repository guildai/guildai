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
import guild.resource

from guild import cli
from guild import config
from guild import modelfile

log = logging.getLogger("core")

def cwd_desc(cwd=None):
    """Returns a description for cwd.

    If cwd the system cwd, returns "this directory" otherwise returns
    the quoted cwd.

    This is used in messages to the user where the cwd is referenced.
    """
    cwd = cwd or config.cwd()
    if os.path.abspath(cwd) == os.path.abspath(os.getcwd()):
        return "the current directory"
    else:
        return "'%s'" % cwd

def cwd_modelfile_path(cwd=None):
    """Returns the path of the modelfile for the cwd.

    Returns None if a modefile doesn't exist in the cwd.
    """
    cwd = cwd or config.cwd()
    for name in modelfile.NAMES:
        path = os.path.join(cwd, name)
        if os.path.exists(path):
            return path
    return None

def cwd_modelfile(cwd=None):
    """Returns the modelfile of the context cwd.

    Returns None if a modelfile doesn't exist in the cwd.
    """
    cwd = cwd or config.cwd()
    try:
        return modelfile.from_dir(cwd)
    except (modelfile.NoModels, IOError):
        return None

def cwd_modeldef(cwd=None):
    """Returns a loaded modeldef for the cwd.

    If a modelfile doesn't exist in the cwd returns None.

    If an error occurs when loading the modelfile, logs a warning
    message and returns None.
    """
    cwd = cwd or config.cwd()
    try:
        return modelfile.from_dir(cwd)
    except (modelfile.NoModels, IOError):
        return None
    except Exception as e:
        log.warning("unable to load modelfile from %s: %s", cwd, e)
        return None

def init_model_path(force_all=False, notify_force_all_option=None, cwd=None):
    """Initializes the model path.

    If the context cwd contains a model def, the path is initialized
    so that only models associated with the cwd are available via
    `guild.model`. An exception to this is when `force_all` is true,
    in which case all models including those in the cwd will be
    available.
    """
    maybe_model_path = cwd or config.cwd()
    if cwd_modelfile_path(maybe_model_path):
        model_path = maybe_model_path
        if force_all:
            guild.model.insert_path(model_path)
        else:
            _maybe_notify_models_limited(notify_force_all_option, model_path)
            guild.model.set_path([model_path])

def _maybe_notify_models_limited(force_all_option, cwd):
    if force_all_option:
        cli.note_once(
            "Limiting models to %s (use %s to include all)"
            % (cwd_desc(cwd), force_all_option))

def init_resource_path(force_all=False, notify_force_all_option=None, cwd=None):
    """Initializes the resource path.

    The same rules in `init_model_path` are applied here to the
    resource path.
    """
    maybe_model_path = cwd or config.cwd()
    if cwd_modelfile_path(maybe_model_path):
        model_path = maybe_model_path
        if force_all:
            guild.resource.insert_path(model_path)
        else:
            _maybe_notify_resources_limited(notify_force_all_option, model_path)
            guild.resource.set_path([model_path])

def _maybe_notify_resources_limited(force_all_option, cwd):
    if force_all_option:
        cli.note_once(
            "Limiting resources to %s (use %s to include all)"
            % (cwd_desc(cwd), force_all_option))
