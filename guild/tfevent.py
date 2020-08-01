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

"""Utility module for TensorFlow events.

It's safe to import this module even when TensorFlow isn't installed
as all required external modules are lazily loaded.
"""

from __future__ import absolute_import
from __future__ import division

import glob
import hashlib
import logging
import os

log = logging.getLogger("guild")


class EventReader(object):
    def __init__(self, dir, all_events=False):
        self.dir = dir
        self.all_events = all_events

    def __iter__(self):
        """Yields event for all available events in dir."""
        from guild.plugins import tensorboard

        try:
            for event in tensorboard.iter_tf_events(self.dir):
                if self.all_events or event.HasField("summary"):
                    yield event
        except Exception as e:
            # PEP 479 landed in Python 3.7 and TB triggers this
            # runtime error when there are no events to read.
            if e.args and e.args[0] == "generator raised StopIteration":
                return
            _log_tfevent_iter_error(self.dir, e)


def _log_tfevent_iter_error(dir, e):
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.exception("reading events from %s", dir)
    else:
        log.warning("error reading TF event from %s: %s", dir, e)


class ScalarReader(object):
    def __init__(self, dir):
        self.dir = dir

    def __iter__(self):
        """Yields (tag, val, step) for all scalars in dir."""
        for event in EventReader(self.dir):
            for val in event.summary.value:
                scalar_info = _try_scalar_event(event, val)
                if scalar_info is not None:
                    yield scalar_info


def _try_scalar_event(event, val):
    if val.HasField("tensor"):
        scalar_val = _try_tensor_scalar(val)
        if scalar_val is not None:
            return val.tag, scalar_val, event.step
    elif val.HasField("simple_value"):
        return val.tag, val.simple_value, event.step
    return None


def _try_tensor_scalar(val):
    from guild.plugins import tensorboard

    if not _is_float_tensor(val.tensor):
        return None
    ndarray = tensorboard.make_ndarray(val.tensor)
    try:
        return ndarray.item()
    except ValueError:
        return None


def _is_float_tensor(t):
    # See tensorboard.compat.tensorflow_stub.dtypes for float types (1
    # and 2).
    return t.dtype in (1, 2)


def scalar_readers(root_path):
    """Returns an iterator that yields (dir, digest, reader) tuples.

    For each yielded events dir, `digest` changes whenever events have
    been written to the dir.

    `reader` is an instance of ScalarReader that can be used to read
    scalars in dir.
    """
    _ensure_tb_logging_patched()
    for subdir_path in _tfevent_subdirs(root_path):
        digest = _event_files_digest(subdir_path)
        yield subdir_path, digest, ScalarReader(subdir_path)


def _tfevent_subdirs(dir):
    for root, dirs, files in os.walk(dir, followlinks=True):
        _del_non_run_linked_dirs(dirs, root)
        if any(_is_event_file(name) for name in files):
            yield root


def _del_non_run_linked_dirs(dirs, root):
    """Removes dirs that are links but not runs."""
    for name in list(dirs):
        path = os.path.join(root, name)
        if not os.path.islink(path):
            continue
        if _is_run(path):
            continue
        dirs.remove(name)


def _is_run(dir):
    opref_path = os.path.join(dir, ".guild", "opref")
    return os.path.exists(opref_path)


def _is_event_file(name):
    return ".tfevents." in name


def _event_files_digest(dir):
    """Returns a digest for dir that changes when events change.

    The digest includes the list of event logs and their associated
    sizes.
    """
    event_files = sorted(glob.glob(os.path.join(dir, "*.tfevents.*")))
    to_hash = "\n".join(
        [
            "{}\n{}".format(filename, os.path.getsize(filename))
            for filename in event_files
            if os.path.isfile(filename)
        ]
    )
    return hashlib.md5(to_hash.encode("utf-8")).hexdigest()


def _ensure_tb_logging_patched():
    """Patch tb logging to supress noisy info and debug logs.

    TB has become very chatty and we want to control our logs. We
    disable outright info and debug logs here.
    """
    from guild.plugins import tensorboard

    tensorboard.silence_info_logging()
