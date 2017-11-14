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

import datetime
import errno
import logging
import sys

from whoosh import fields
from whoosh import index
from whoosh import query

import guild.opref
import guild.run

from guild import util
from guild import var

if sys.version_info[0] == 2:
    _u = unicode
else:
    _u = str

log = logging.getLogger("core")

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
        schema.add("priv_*", fields.STORED, glob=True)
        return schema

    def get_run(self, run_id):
        with self.ix.searcher() as seacher:
            hits = seacher.search(query.Term("run_id", run_id))
            if hits:
                assert len(hits) == 1, hits
                return self._reindex_changed_run(run_id, hits[0].fields())
            else:
                return self._index_run(run_id)

    def _reindex_changed_run(self, run_id, fields):
        run = var.get_run(run_id)
        changed = self._changed_fields(run, fields)
        if not changed:
            return fields
        log.debug("reindexing run %s (fields: %s)", run_id, list(changed))
        new = {}
        new.update(fields)
        new.update(changed)
        writer = self.ix.writer()
        writer.update_document(**new)
        writer.commit()
        return new

    def _changed_fields(self, run, fields):
        changed = {}
        changed.update(self._changed_attrs(run, fields))
        return changed

    def _changed_attrs(self, run, fields):
        changed = {}
        changed.update(self._maybe_status_field(fields, run))
        changed.update(self._maybe_opref_fields(fields, run))
        changed.update(self._maybe_flag_fields(fields, run))
        changed.update(self._maybe_label_field(fields, run))
        changed.update(self._maybe_attr_field(fields, "started", run))
        changed.update(self._maybe_attr_field(fields, "stopped", run))
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

    @staticmethod
    def _flag_field_name(name, val_type):
        if val_type is int:
            return "flagi_{}".format(name)
        elif val_type is float:
            return "flagf_{}".format(name)
        elif val_type is bool:
            return "flagb_{}". format(name)
        else:
            return "flags_{}".format(name)

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

    def _index_run(self, run_id):
        log.debug("indexing run %s", run_id)
        run = var.get_run(run_id)
        writer = self.ix.writer()
        fields = dict(
            id=_u(run_id),
            short_id=guild.run.run_short_id(run_id),
        )
        fields.update(self._changed_attrs(run, fields))
        writer.add_document(**fields)
        writer.commit()
        return fields
