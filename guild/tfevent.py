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
        try:
            from tensorboard.backend.event_processing import event_accumulator
        except ImportError:
            pass
        else:
            events = event_accumulator._GeneratorFromPath(self.dir).Load()
            for event in events:
                if not event.HasField("summary"):
                    continue
                for val in event.summary.value:
                    if not val.HasField("simple_value"):
                        continue
                    yield val.tag, val.simple_value, event.step

def iter_events(root_path):
    """Returns an iterator that yields (dir, digest, reader) tuples.

    For each yielded events dir, `digest` changes whenever events have
    been written to the dir.

    `reader` is an instance of ScalarReader that can be used to read
    scalars in dir.
    """
    ensure_tf_logging_patched()
    try:
        from tensorboard.backend.event_processing import io_wrapper
    except ImportError:
        pass
    else:
        for subdir_path in io_wrapper.GetLogdirSubdirectories(root_path):
            if _linked_resource_path(subdir_path, root_path):
                log.debug("skipping linked resource path %s", subdir_path)
                continue
            digest = _event_files_digest(subdir_path)
            yield subdir_path, digest, ScalarReader(subdir_path)

def _linked_resource_path(path, root):
    """Returns True if path is a linked resource under root.

    This is used to exclude tfevents under root that are linked
    resources.
    """
    if _has_steps(root):
        return _links_under_root(path, root) > 1
    else:
        return not _real_path_under_root(path, root)

def _has_steps(path):
    return os.path.exists(os.path.join(path, ".guild", "attrs", "steps"))

def _links_under_root(path, root):
    """Returns the number of links to path uses user root."""
    links = 0
    last_path = None
    while path != root and path != last_path:
        if os.path.islink(path):
            links += 1
        last_path = path
        path = os.path.dirname(path)
    return links

def _real_path_under_root(path, root):
    """Returns True if real path is under root."""
    real_path = os.path.realpath(path)
    real_root = os.path.realpath(root)
    return real_path.startswith(real_root)

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

def ensure_tf_logging_patched():
    _ensure_tf_oldstyle_logging_patched()
    _ensure_tf_newstyle_logging_patched()

def _ensure_tf_oldstyle_logging_patched():
    try:
        from tensorflow import logging
    except ImportError:
        pass
    else:
        logging.info = logging.debug = lambda *_arg, **_kw: None

def _ensure_tf_newstyle_logging_patched():
    try:
        from tensorboard.util import tb_logging
    except ImportError:
        pass
    else:
        logger = tb_logging.get_logger()
        logger.info = logger.debug = lambda *_arg, **_kw: None
