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

from __future__ import absolute_import
from __future__ import division

import base64
import errno
import glob
import hashlib
import logging
import os
import random
import re
import time
import sys

import six

from whoosh import fields
from whoosh import index
from whoosh import query

from guild import util
from guild import var

if sys.version_info[0] == 2:
    # pylint: disable=undefined-variable
    _u = unicode
else:
    _u = str

log = logging.getLogger("guild")

class RunResult(object):

    def __init__(self, fields):
        self._fs = fields

    @property
    def id(self):
        return self._fs.get("id")

    @property
    def short_id(self):
        return self._fs.get("short_id")

    @property
    def status(self):
        return self._fs.get("status")

    @property
    def started(self):
        return self._fs.get("started")

    @property
    def stopped(self):
        return self._fs.get("stopped")

    @property
    def pkg_type(self):
        return self._fs.get("pkg_type")

    @property
    def pkg_name(self):
        return self._fs.get("pkg_name")

    @property
    def pkg_version(self):
        return self._fs.get("pkg_version")

    @property
    def model_name(self):
        return self._fs.get("model_name")

    @property
    def op_name(self):
        return self._fs.get("op_name")

    @property
    def label(self):
        return self._fs.get("label")

    def scalar(self, key_or_keys, default=None):
        if isinstance(key_or_keys, str):
            return self._scalar(key_or_keys, default)
        else:
            for key in key_or_keys:
                maybe_val = self._scalar(key, None)
                if maybe_val is not None:
                    return maybe_val
            return default

    def _scalar(self, key, default):
        field_name = _encode_field_name("scalar_", key)
        return self._fs.get(field_name, default)

    def iter_flags(self):
        for name in self._fs:
            for prefix in ["flagi_", "flagf_", "flagb_", "flags_"]:
                try:
                    flag_name = _decode_field_name(prefix, name)
                except ValueError:
                    pass
                else:
                    yield flag_name, self._fs[name]
                    break

    def iter_scalars(self):
        for name in self._fs:
            if not name.startswith("scalar_"):
                continue
            try:
                scalar_key = _decode_field_name("scalar_", name)
            except ValueError:
                pass
            else:
                yield scalar_key, self._fs[name]

class RunIndex(object):

    def __init__(self):
        self.path = var.cache_dir("runs")
        self._ix = None

    @property
    def ix(self):
        if self._ix is None:
            self._ix = self._init_index()
        return self._ix

    def _init_index(self):
        try:
            return index.open_dir(self.path)
        except index.EmptyIndexError:
            return self._create_index()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            util.ensure_dir(self.path)
            return self._create_index()

    def _create_index(self):
        util.ensure_dir(self.path)
        return index.create_in(self.path, self._init_schema())

    @staticmethod
    def _init_schema():
        schema = fields.Schema()
        schema.add("id", fields.ID(unique=True, stored=True))
        schema.add("short_id", fields.ID(stored=True))
        schema.add("status", fields.ID(stored=True))
        schema.add("started", fields.NUMERIC(int, bits=64, stored=True))
        schema.add("stopped", fields.NUMERIC(int, bits=64, stored=True))
        schema.add("pkg_type", fields.ID(stored=True))
        schema.add("pkg_name", fields.ID(stored=True))
        schema.add("pkg_version", fields.ID(stored=True))
        schema.add("model_name", fields.ID(stored=True))
        schema.add("op_name", fields.ID(stored=True))
        schema.add("label", fields.TEXT(stored=True))
        schema.add("scalar_*", fields.NUMERIC(float, stored=True), glob=True)
        schema.add("flagi_*", fields.NUMERIC(int, bits=64, stored=True),
                   glob=True)
        schema.add("flagf_*", fields.NUMERIC(float, stored=True), glob=True)
        schema.add("flagb_*", fields.BOOLEAN(stored=True), glob=True)
        schema.add("flags_*", fields.ID(stored=True), glob=True)
        schema.add("priv_*", fields.STORED, glob=True)
        return schema

    def runs(self, run_ids):
        runs = []
        writer = self._ix_writer()
        with self.ix.searcher() as seacher:
            for run_id in run_ids:
                hits = seacher.search(query.Term("id", run_id), limit=None)
                assert len(hits) <= 1, hits
                hit_fields = hits[0].fields() if hits else None
                try:
                    run = var.get_run(run_id)
                except LookupError:
                    pass
                else:
                    cur_fields = self._ensure_indexed_run(
                        run, hit_fields, writer)
                    runs.append(RunResult(cur_fields))
        writer.commit()
        return runs

    def _ix_writer(self):
        max_retries = 3
        min_wait = 0.1
        max_wait = 0.5
        retries = 0
        while True:
            try:
                return self.ix.writer()
            except index.LockError:
                if retries == max_retries:
                    raise
                retries += 1
                time.sleep(random.uniform(min_wait, max_wait))

    def _ensure_indexed_run(self, run, cur_fields, writer):
        if cur_fields:
            return self._reindex_changed_run(run, cur_fields, writer)
        else:
            return self._index_run(run, writer)

    def _reindex_changed_run(self, run, fields, writer):
        changed = self._changed_fields(run, fields)
        if not changed:
            log.debug("skipping run %s (unchanged)", run.id)
            return fields
        log.debug(
            "reindexing run %s (%i field(s) changed)",
            run.id, len(changed))
        new = {}
        new.update(fields)
        new.update(changed)
        writer.update_document(**new)
        return new

    def _changed_fields(self, run, fields):
        changed = {}
        changed.update(self._maybe_status_field(fields, run))
        changed.update(self._maybe_opref_fields(fields, run))
        changed.update(self._maybe_flag_fields(fields, run))
        changed.update(self._maybe_label_field(fields, run))
        changed.update(self._maybe_attr_field(fields, "started", run))
        changed.update(self._maybe_attr_field(fields, "stopped", run))
        changed.update(self._maybe_scalars(fields, run))
        return changed

    @staticmethod
    def _maybe_status_field(fields, run):
        status = _u(run.status)
        return {"status": status} if status != fields.get("status") else {}

    @staticmethod
    def _maybe_opref_fields(fields, run):
        if "priv_has_opref" in fields or not run.opref:
            return {}
        opref = run.opref
        return {
            "pkg_type": _u(opref.pkg_type),
            "pkg_name": _u(opref.pkg_name),
            "pkg_version": _u(opref.pkg_version),
            "model_name": _u(opref.model_name),
            "op_name": _u(opref.op_name),
            "priv_has_opref": True,
            }

    def _maybe_flag_fields(self, fields, run):
        if "priv_has_flags" in fields or not run.has_attr("flags"):
            return {}
        fields = self._flag_fields(run)
        fields["priv_has_flags"] = True
        return fields

    @staticmethod
    def _flag_fields(run):
        fields = {}
        for flag_name, val in run.get("flags", {}).items():
            if isinstance(val, int):
                field_name = _encode_field_name("flagi_", flag_name)
            elif isinstance(val, float):
                field_name = _encode_field_name("flagf_", flag_name)
            elif isinstance(val, bool):
                field_name = _encode_field_name("flagb_", flag_name)
            else:
                field_name = _encode_field_name("flags_", flag_name)
                val = _u(val) if val is not None else u""
            fields[field_name] = val
        return fields

    @staticmethod
    def _maybe_label_field(fields, run):
        label = _u(run.get("label", ""))
        return {"label": label} if label != fields.get("label") else {}

    def _maybe_attr_field(self, fields, attr_name, run):
        marker = "priv_has_{}".format(attr_name)
        if marker in fields or not run.has_attr(attr_name):
            return {}
        return {
            attr_name: self._field_val(run.get(attr_name), attr_name),
            marker: True,
        }

    def _field_val(self, val, attr_name):
        assert self._ix
        field = self._ix.schema[attr_name]
        return _u(val) if isinstance(field, (fields.ID, fields.TEXT)) else val

    def _maybe_scalars(self, fields, run):
        from tensorboard.backend.event_processing import io_wrapper
        from tensorboard.backend.event_processing import event_accumulator
        from guild import tfevent
        tfevent.ensure_tf_logging_patched()
        scalars = {}
        scalar_aliases = self._init_scalar_aliases(run)
        for path in io_wrapper.GetLogdirSubdirectories(run.path):
            if not self._path_in_run(path, run):
                log.debug("%s is not part of run %s, skipping", path, run.id)
                continue
            events_checksum_field_name = self._events_checksum_field_name(path)
            last_checksum = fields.get(events_checksum_field_name)
            cur_checksum = self._events_checksum(path)
            log.debug(
                "event path checksums for %s: last=%s, cur=%s",
                path, last_checksum, cur_checksum)
            if last_checksum != cur_checksum:
                log.debug("indexing events in %s", path)
                rel_path = os.path.relpath(path, run.path)
                events = event_accumulator._GeneratorFromPath(path).Load()
                scalar_vals = self._scalar_vals(events, rel_path)
                self._apply_scalar_vals(scalar_vals, scalars, scalar_aliases)
                scalars[events_checksum_field_name] = cur_checksum
        return scalars

    @staticmethod
    def _init_scalar_aliases(run):
        """Returns list of scalar aliases as `key`, `pattern` tuples.

        `key` is the mapped scalar key and `pattern` is the associated
        scalar key pattern. If a logged scalar key matches `pattern`,
        `key` is treated as an alias of the logged scalar key.
        """
        attr = run.get("_extra_scalars", {})
        if not isinstance(attr, dict):
            log.debug(
                "unexpected type for _extra_scalar: %s",
                type(attr))
            return []
        aliases = []
        for key, patterns in sorted(attr.items()):
            if isinstance(patterns, six.string_types):
                patterns = [patterns]
            for p in patterns:
                try:
                    compiled_p = re.compile(p)
                except Exception:
                    log.debug("invalid alias pattern for %s: %s", key, p)
                else:
                    aliases.append((key, compiled_p))
        return aliases

    @staticmethod
    def _path_in_run(path, run):
        """Returns True if `path` is in run or False not.

        `path` may be a link to another run.
        """
        real_path = os.path.realpath(path)
        real_run_dir = os.path.realpath(run.path)
        return real_path.startswith(real_run_dir)

    @staticmethod
    def _events_checksum_field_name(path):
        """Returns a field name that is unique for any given path."""
        abs_path = os.path.abspath(path)
        path_digest = hashlib.md5(abs_path.encode("utf-8")).hexdigest()
        return "priv_events_checksum_{}".format(path_digest)

    @staticmethod
    def _events_checksum(path):
        """Returns a checksum for path that changes when events change.

        We use a directory watcher (by way of event_accumulator) to
        load events from path. We want a checksum that changes
        whenever an event under path is added. We do this by returning
        a digest of the event logs and their associated sizes.
        """
        event_paths = sorted(glob.glob(os.path.join(path, "*.tfevents.*")))
        to_hash = "\n".join([
            "{}\n{}".format(event_path, os.path.getsize(event_path))
            for event_path in event_paths
            if os.path.isfile(event_path)])
        return hashlib.md5(to_hash.encode("utf-8")).hexdigest()

    def _scalar_vals(self, events, events_prefix):
        all_vals = {}
        for event in events:
            if not event.HasField("summary"):
                continue
            for val in event.summary.value:
                if not val.HasField("simple_value"):
                    continue
                scalar_key = self._scalar_key(val.tag, events_prefix)
                scalar_vals = all_vals.setdefault(scalar_key, [])
                scalar_vals.append((val.simple_value, event.step))
        return all_vals

    @staticmethod
    def _scalar_key(tag, path_prefix):
        if not path_prefix or path_prefix == ".":
            return tag
        else:
            return os.path.normpath(path_prefix) + "/" + tag

    def _apply_scalar_vals(self, scalar_vals, scalars, aliases):
        for key, vals in scalar_vals.items():
            if not vals:
                continue
            self._store_scalar_vals(key, vals, scalars)
            for alias_key in self._alias_keys(key, aliases):
                log.debug("using alias %s for %s", alias_key, key)
                self._store_scalar_vals(alias_key, vals, scalars)

    @staticmethod
    def _store_scalar_vals(key, vals, scalars):
        last_val, step = vals[-1]
        scalars[_encode_field_name("scalar_", key)] = last_val
        scalars[_encode_field_name("scalar_", key + "_step")] = step

    @staticmethod
    def _alias_keys(logged_key, aliases):
        for alias, pattern in aliases:
            if pattern.match(logged_key):
                yield alias

    def _index_run(self, run, writer):
        log.debug("indexing run %s", run.id)
        fields = dict(
            id=_u(run.id),
            short_id=run.short_id,
        )
        fields.update(self._changed_fields(run, fields))
        writer.add_document(**fields)
        return fields

    def sync(self):
        runs = {
            run.id: run for run in var.runs()
        }
        reader = self.ix.reader()
        writer = self.ix.writer()
        for docnum, fields in reader.iter_docs():
            run_id = fields["id"]
            run = runs.pop(run_id, None)
            if run:
                self._reindex_changed_run(run, fields, writer)
            else:
                self._delete_run(docnum, run_id, writer)
        for run in runs.values():
            self._index_run(run, writer)
        log.debug("committing changes")
        # We'd like to use commit(optimize=True here but there's a bug
        # that causes our 'priv_xxx' fields to be deleted. See
        # https://bitbucket.org/mchaput/whoosh/issues/472 for details.
        writer.commit()

    @staticmethod
    def _delete_run(docnum, run_id, writer):
        log.debug("deleting run %s", run_id)
        writer.delete_document(docnum)

def _encode_field_name(prefix, to_encode):
    to_encode = to_encode.replace("=", "_").encode("utf-8")
    encoded = base64.b32encode(to_encode)
    return prefix + encoded.decode("utf-8")

def _decode_field_name(prefix, field_name):
    if not field_name.startswith(prefix):
        raise ValueError((prefix, field_name))
    encoded = field_name[len(prefix):]
    return base64.b32decode(encoded.replace("_", "="))

def _patch_whoosh_write_pickle():
    # See https://bitbucket.org/mchaput/whoosh/issues/473
    from whoosh.filedb.structfile import StructFile
    write_pickle_orig = StructFile.write_pickle
    def write_pickle(self, ob):
        write_pickle_orig(self, ob, protocol=2)
    StructFile.write_pickle = write_pickle

_patch_whoosh_write_pickle()
