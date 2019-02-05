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

import logging
import os
import sqlite3

from guild import op_util
from guild import tfevent
from guild import util
from guild import var

log = logging.getLogger("guild")

VERSION = 1
DB_NAME = "index_v%i.db" % VERSION

class AttrReader(object):

    def __init__(self):
        self._data = {}

    def refresh(self, runs):
        self._data = self._runs_data(runs)

    def _runs_data(self, runs):
        return {run.id: self._run_data(run) for run in runs}

    def _run_data(self, run):
        opref = run.opref
        started = run.get("started")
        stopped = run.get("stopped")
        status = run.status
        return {
            "id": run.id,
            "run": run.short_id,
            "model": opref.model_name,
            "operation": op_util.format_op_desc(run),
            "op": opref.op_name,
            "started": util.format_timestamp(started),
            "stopped": util.format_timestamp(stopped),
            "status": status,
            "time": self._duration(status, started, stopped),
        }

    @staticmethod
    def _duration(status, started, stopped):
        if status == "running":
            return util.format_duration(started)
        elif stopped:
            return util.format_duration(started, stopped)
        return None

    def read(self, run, attr):
        run_data = self._data.get(run.id, {})
        try:
            return run_data[attr]
        except KeyError:
            return run.get(attr)

class FlagReader(object):

    def __init__(self):
        self._data = {}

    def refresh(self, runs):
        self._data = {
            run.id: run.get("flags", {})
            for run in runs
        }

    def read(self, run, flag):
        return self._data.get(run.id, {}).get(flag)

class ScalarReader(object):

    _col_index_map = {
        ("first", False): 3,
        ("first", True): 4,
        ("last", False): 5,
        ("last", True): 6,
        ("min", False): 7,
        ("min", True): 8,
        ("max", False): 9,
        ("max", True): 10,
        ("avg", False): 11,
        ("total", False): 12,
        ("count", False): 13,
    }

    def __init__(self, db):
        self._db = db

    def refresh(self, runs):
        for run in runs:
            for path, cur_digest, scalars in tfevent.iter_events(run.path):
                log.debug("found events in %s (digest %s)", path, cur_digest)
                prefix = self._scalar_prefix(path, run.path)
                last_digest = self._scalar_source_digest(run.id, prefix)
                if cur_digest != last_digest:
                    log.debug(
                        "last digest for %s (%s) is stale, refreshing scalars",
                        path, last_digest or 'unset')
                    summarized = self._summarize_scalars(scalars)
                    if last_digest:
                        self._del_scalars(run.id, prefix)
                    self._write_summarized(run.id, prefix, summarized)
                    self._write_source_digest(run.id, prefix, cur_digest)

    @staticmethod
    def _scalar_prefix(scalars_path, root):
        rel_path = os.path.relpath(scalars_path, root)
        if rel_path in (".", ".guild"):
            return ""
        return rel_path.replace(os.sep, "/")

    def _scalar_source_digest(self, run_id, prefix):
        cur = self._db.execute("""
          SELECT path_digest FROM scalar_source
          WHERE run = ? AND prefix = ?
        """, (run_id, prefix))
        row = cur.fetchone()
        if not row:
            return None
        return row[0]

    @staticmethod
    def _summarize_scalars(scalars):
        summarized = {}
        for tag, val, step in scalars:
            try:
                tag_summary = summarized[tag]
            except KeyError:
                summarized[tag] = tag_summary = TagSummary()
            tag_summary.add(val, step)
        return summarized

    def _del_scalars(self, run_id, prefix):
        self._db.execute("""
          DELETE from scalar
          WHERE run = ? AND prefix = ?
        """, (run_id, prefix))

    def _write_summarized(self, run_id, prefix, summarized):
        cur = self._db.cursor()
        for tag in summarized:
            tsum = summarized[tag]
            cur.execute("""
              INSERT INTO scalar
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                prefix,
                tag,
                tsum.first_val,
                tsum.first_step,
                tsum.last_val,
                tsum.last_step,
                tsum.min_val,
                tsum.min_step,
                tsum.max_val,
                tsum.max_step,
                tsum.avg_val,
                tsum.total,
                tsum.count
            ))
        self._db.commit()

    def _write_source_digest(self, run_id, prefix, path_digest):
        cur = self._db.cursor()
        cur.execute("""
          UPDATE scalar_source
            SET path_digest = ?
            WHERE run = ? AND prefix = ?
        """, (path_digest, run_id, prefix))
        cur.execute("""
          INSERT OR IGNORE INTO scalar_source
          VALUES (?, ?, ?)
        """, (run_id, prefix, path_digest))
        self._db.commit()

    def read(self, run, prefix, tag, qual, step):
        col_index = self._read_col_index(qual, step)
        cur = self._db.cursor()
        if prefix is None:
            cur.execute("""
              SELECT * FROM scalar
              WHERE run = ? AND tag = ?
            """, (run.id, tag))
        else:
            cur.execute("""
              SELECT * FROM scalar
              WHERE run = ? AND prefix LIKE ? AND tag = ?
              ORDER BY prefix, tag
            """, (run.id, "%s%%" % prefix, tag))
        row = cur.fetchone()
        if not row:
            return None
        return row[col_index]

    def _read_col_index(self, qual, step):
        try:
            return self._col_index_map[(qual or "last", step)]
        except KeyError:
            raise ValueError(
                "unsupported scalar type qual=%r step=%s"
                % (qual, step))

    def iter_scalars(self, run):
        cur = self._db.execute("""
          SELECT prefix, tag FROM scalar
          WHERE run = ?
          ORDER BY 'prefix', 'tag'
        """, (run.id,))
        for row in cur.fetchall():
            yield {
                "prefix": row[0],
                "tag": row[1],
            }

class TagSummary(object):

    def __init__(self):
        self.first_val = None
        self.first_step = None
        self.last_val = None
        self.last_step = None
        self.min_val = None
        self.min_step = None
        self.max_val = None
        self.max_step = None
        self.avg_val = None
        self.total = 0
        self.count = 0

    def add(self, val, step):
        self._set_first(val, step)
        self._set_last(val, step)
        self._set_min(val, step)
        self._set_max(val, step)
        self.total += val
        self.count += 1
        self.avg_val = self.total / self.count

    def _set_first(self, val, step):
        if self.first_step is None or step < self.first_step:
            self.first_val = val
            self.first_step = step

    def _set_last(self, val, step):
        if self.last_step is None or step > self.last_step:
            self.last_val = val
            self.last_step = step

    def _set_min(self, val, step):
        if self.min_val is None or val < self.min_val:
            self.min_val = val
            self.min_step = step

    def _set_max(self, val, step):
        if self.max_val is None or val > self.max_val:
            self.max_val = val
            self.max_step = step

class RunIndex(object):
    """Interface for using a run index."""

    def __init__(self, path=None):
        self.path = path or var.cache_dir("runs")
        self._db = self._init_db()
        self._attr_reader = AttrReader()
        self._flag_reader = FlagReader()
        self._scalar_reader = ScalarReader(self._db)

    def _init_db(self):
        db_path = self._db_path()
        util.ensure_dir(os.path.dirname(db_path))
        db = sqlite3.connect(db_path)
        self._init_tables(db)
        return db

    def _db_path(self):
        return os.path.join(self.path, DB_NAME)

    @staticmethod
    def _init_tables(db):
        db.execute("""
          CREATE TABLE IF NOT EXISTS scalar (
            run,
            prefix,
            tag,
            first_val,
            first_step,
            last_val,
            last_step,
            min_val,
            min_step,
            max_val,
            max_step,
            avg_val,
            total,
            count
          )
        """)
        db.execute("""
          CREATE INDEX IF NOT EXISTS scalar_i
          ON scalar (run, prefix, tag)
        """)
        db.execute("""
          CREATE TABLE IF NOT EXISTS scalar_source (
            run,
            prefix,
            path_digest
          )
        """)
        db.execute("""
          CREATE UNIQUE INDEX IF NOT EXISTS scalar_source_pk
          ON scalar_source (run, prefix)
        """)

    def refresh(self, runs, types=None):
        """Refreshes the index for the specified runs.

        `runs` is list of runs or run IDs for each run to refresh.

        `types` is an optional list of data types to refresh.
        """
        if types is None or "attr" in types:
            self._attr_reader.refresh(runs)
        if types is None or "flag" in types:
            self._flag_reader.refresh(runs)
        if types is None or "scalar" in types:
            self._scalar_reader.refresh(runs)

    def _run_val_readers(self, _run):
        return self._base_readers

    def run_attr(self, run, name):
        return self._attr_reader.read(run, name)

    def run_flag(self, run, name):
        return self._flag_reader.read(run, name)

    def run_scalar(self, run, prefix, tag, qual, step):
        return self._scalar_reader.read(run, prefix, tag, qual, step)

    def run_scalars(self, run):
        return list(self._scalar_reader.iter_scalars(run))
