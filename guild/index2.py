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

import os
import sqlite3

from guild import opref as opreflib
from guild import util
from guild import var

VERSION = 2
DB_NAME = "index%i.db" % VERSION

class RunIndex(object):
    """Interface for using a run index."""

    def __init__(self, path=None):
        self.path = path or var.cache_dir("runs")
        self._db = self._init_db()
        self._attr_reader = AttrReader()

    def _init_db(self):
        db = sqlite3.connect(self._db_path())
        self._init_tables(db)
        return db

    def _db_path(self):
        return os.path.join(self.path, DB_NAME)

    @staticmethod
    def _init_tables(db):
        cur = db.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS run_val (
              run,
              source,
              name,
              qual,
              val,
              step
            )
            """)
        cur.execute(
            """CREATE TABLE IF NOT EXISTS source (
              run,
              path,
              last_read_size,
              last_read_mtime
            )
            """)
        db.commit()

    def refresh(self, runs):
        """Refreshes the index for the specified runs.

        `runs` is list of runs or run IDs for each run to refresh.
        """
        self._attr_reader.refresh(runs)

    def _run_val_readers(self, _run):
        return self._base_readers

    def run_attr(self, run, name):
        return self._attr_reader.read(run, name)

class AttrReader(object):

    def __init__(self):
        self._data = {}

    def refresh(self, runs):
        self._data = self._runs_data(runs)

    def _runs_data(self, runs):
        return {run.id: self._run_data(run) for run in runs}

    def _run_data(self, run):
        opref = opreflib.OpRef.from_run(run)
        started = run.get("started")
        stopped = run.get("stopped")
        status = run.status
        return {
            "id": run.id,
            "run": run.short_id,
            "model": opref.model_name,
            "operation": opref.op_name,
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
