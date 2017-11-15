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

import base64
import datetime
import errno
import glob
import logging
import md5
import os
import sys

from whoosh import fields
from whoosh import index
from whoosh import query

import guild.opref

from guild import util
from guild import var

if sys.version_info[0] == 2:
    _u = unicode
else:
    _u = str

log = logging.getLogger("core")

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
        field_name = _encoded_field_name("scalar_", key)
        return self._fs.get(field_name, default)

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
        return index.create_in(self.path, self._init_schema())

    @staticmethod
    def _init_schema():
        schema = fields.Schema()
        schema.add("id", fields.ID(unique=True, stored=True))
        schema.add("short_id", fields.ID(stored=True))
        schema.add("status", fields.ID(stored=True))
        schema.add("started", fields.DATETIME(stored=True))
        schema.add("stopped", fields.DATETIME(stored=True))
        schema.add("pkg_type", fields.ID(stored=True))
        schema.add("pkg_name", fields.ID(stored=True))
        schema.add("pkg_version", fields.ID(stored=True))
        schema.add("model_name", fields.ID(stored=True))
        schema.add("op_name", fields.ID(stored=True))
        schema.add("label", fields.TEXT(stored=True))
        schema.add("scalar_*", fields.NUMERIC(float, stored=True), glob=True)
        schema.add("flagi_*", fields.NUMERIC(int, stored=True), glob=True)
        schema.add("flagf_*", fields.NUMERIC(int, stored=True), glob=True)
        schema.add("flagb_*", fields.BOOLEAN(stored=True), glob=True)
        schema.add("flags_*", fields.ID(stored=True), glob=True)
        schema.add("priv_*", fields.STORED, glob=True)
        return schema

    def runs(self, run_ids):
        runs = []
        writer = self.ix.writer()
        with self.ix.searcher() as seacher:
            for run_id in run_ids:
                run = var.get_run(run_id)
                hits = seacher.search(query.Term("id", run_id))
                assert len(hits) <= 1, hits
                hit_fields = hits[0].fields() if hits else None
                cur_fields = self._ensure_indexed_run(run, hit_fields, writer)
                runs.append(RunResult(cur_fields))
        writer.commit()
        return runs

    def _ensure_indexed_run(self, run, cur_fields, writer):
        if cur_fields:
            return self._reindex_changed_run(run, cur_fields, writer)
        else:
            return self._index_run(run, writer)

    def _reindex_changed_run(self, run, fields, writer):
        changed = self._changed_fields(run, fields)
        if not changed:
            return fields
        log.debug("reindexing run %s (fields: %s)", run.id, list(changed))
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
        if "priv_has_opref" in fields or not run.has_attr("opref"):
            return {}
        opref = guild.opref.OpRef.from_run(run)
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

    def _flag_fields(self, run):
        return {
            self._flag_field_name(name, type(val)): self._field_val(val)
            for name, val in run.get("flags", {}).items()
        }

    def _flag_field_name(self, name, val_type):
        return _encoded_field_name(self._flag_field_prefix(val_type), name)

    @staticmethod
    def _flag_field_prefix(val_type):
        if val_type is int:
            return "flagi_"
        elif val_type is float:
            return "flagf_"
        elif val_type is bool:
            return "flagb_"
        else:
            return "flags_"

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

    def _field_val(self, val, attr_name=None):
        assert self._ix
        if attr_name is None:
            return _u(val) if isinstance(val, str) else val
        field = self._ix.schema[attr_name]
        if isinstance(field, fields.DATETIME):
            return datetime.datetime.fromtimestamp(val / 1000000)
        else:
            return _u(val) if isinstance(val, str) else val

    def _maybe_scalars(self, fields, run):
        from tensorboard.backend.event_processing import event_multiplexer
        from tensorboard.backend.event_processing import event_accumulator
        _ensure_tf_logger_patched()
        scalars = {}
        for path in event_multiplexer.GetLogdirSubdirectories(run.path):
            events_checksum_field_name = self._events_checksum_field_name(path)
            last_checksum = fields.get(events_checksum_field_name)
            cur_checksum = self._events_checksum(path)
            if last_checksum == cur_checksum:
                continue
            scalars[events_checksum_field_name] = cur_checksum
            log.debug("indexing events in %s", path)
            rel_path = os.path.relpath(path, run.path)
            events = event_accumulator._GeneratorFromPath(path).Load()
            scalar_vals = self._scalar_vals(events, rel_path)
            for key, vals in scalar_vals.items():
                if not vals:
                    continue
                self._store_scalar_vals(key, vals, scalars)
        return scalars

    @staticmethod
    def _events_checksum_field_name(path):
        abs_path = os.path.abspath(path)
        path_digest = md5.md5(abs_path).hexdigest()
        return "priv_events_checksum_{}".format(path_digest)

    @staticmethod
    def _events_checksum(path):
        """Returnds a checksum for path that changes when events change.

        We use a directory watcher (by way of event_accumulator) to
        load events from path. We want a checksum that changes
        whenever an event under path is added. We do this by returning
        a digest of the event logs and their associated sizes.
        """
        event_paths = sorted(glob.glob(os.path.join(path, "*.tfevents.*")))
        to_hash = "\n".join([
            "{}\n{}".format(event_path, os.path.getsize(event_path))
            for event_path in event_paths])
        return md5.md5(to_hash).hexdigest()

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
                scalar_vals.append(val.simple_value)
        return all_vals

    @staticmethod
    def _scalar_key(tag, path_prefix):
        if not path_prefix or path_prefix == ".":
            return tag
        else:
            return os.path.normpath(path_prefix) + "/" + tag

    @staticmethod
    def _store_scalar_vals(key, vals, scalars):
        field_name = _encoded_field_name("scalar_", key)
        last = vals[-1]
        scalars[field_name] = last

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
        pass

def _encoded_field_name(prefix, to_encode):
    encoded = base64.b32encode(to_encode).replace("=", "_")
    return prefix + encoded

def _scalar_field_name(key):
    return "scalar_{}".format(md5.md5(key).hexdigest())

def _ensure_tf_logger_patched():
    from tensorflow import logging
    logging.info = logging.debug = lambda *_arg, **_kw: None
