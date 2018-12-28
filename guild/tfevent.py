# Copyright 2017-2019 TensorHub, Inc.
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

class ScalarReader(object):

    def __init__(self, dir):
        self.dir = dir

    def __iter__(self):
        """Yields (tag, val, step) for scalars.
        """
        from tensorboard.backend.event_processing import event_accumulator
        events = event_accumulator._GeneratorFromPath(self.dir).Load()
        for event in events:
            if not event.HasField("summary"):
                continue
            for val in event.summary.value:
                if not val.HasField("simple_value"):
                    continue
                yield val.tag, val.simple_value, event.step

def iter_events(path):
    """Returns an iterator that yields (dir, digest, reader) tuples.

    For each yielded events dir, `digest` changes whenever events have
    been written to the dir.

    `reader` is an instance of ScalarReader that can be used to read
    scalars in dir.
    """
    _ensure_tf_logger_patched()
    from tensorboard.backend.event_processing import io_wrapper
    for dir in io_wrapper.GetLogdirSubdirectories(path):
        if not _dir_under_path(dir, path):
            log.debug("%s is not under %s, skipping", dir, path)
            continue
        digest = _event_files_digest(dir)
        yield dir, digest, ScalarReader(dir)

def _dir_under_path(dir, path):
    """Returns True if `dir` is under `path`.

    This is used to filter out links outside of path.
    """
    real_dir = os.path.realpath(dir)
    real_path = os.path.realpath(path)
    return real_dir.startswith(real_path)

def _event_files_digest(dir):
    """Returns a digest for dir that changes when events change.

    The digest includes the list of event logs and their associated
    sizes.
    """
    event_files = sorted(glob.glob(os.path.join(dir, "*.tfevents.*")))
    to_hash = "\n".join([
        "{}\n{}".format(filename, os.path.getsize(filename))
        for filename in event_files
        if os.path.isfile(filename)])
    return hashlib.md5(to_hash.encode("utf-8")).hexdigest()

def _ensure_tf_logger_patched():
    from tensorflow import logging
    logging.info = logging.debug = lambda *_arg, **_kw: None
