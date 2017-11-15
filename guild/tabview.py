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

import curses
import logging

from tabview import tabview

from guild import util

ViewerBase = tabview.Viewer

class Viewer(ViewerBase):

    get_data = None
    logs = None

    def __init__(self, *args, **kw):
        assert self.get_data is not None
        with StatusWin("Reading data"):
            data = self._init_data()
        args = (args[0], data) + args[2:]
        # pylint: disable=non-parent-init-called
        ViewerBase.__init__(self, *args, **kw)

    def _init_data(self):
        return tabview.process_data(self.get_data())

    def location_string(self, yp, xp):
        lstr = ViewerBase.location_string(self, yp, xp)
        return lstr.replace("-,", "")

    def define_keys(self):
        ViewerBase.define_keys(self)
        del self.keys["t"]
        if self.logs:
            self.keys["`"] = self.show_logs

    def show_logs(self):
        formatted = self._format_logs()
        tabview.TextBox(self.scr, data=formatted, title="Logs")()
        self.resize()

    def _format_logs(self):
        assert self.logs
        fmt = logging.Formatter("%(asctime)s: %(levelname)s %(message)s")
        return "\n".join([fmt.format(r) for r in self.logs.get_all()])

class StatusWin(object):

    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        scr = curses.initscr()
        scr.clear()
        scr_h, scr_w = scr.getmaxyx()
        win_h, win_w = 5, 25
        win_y = (scr_h - win_h) // 2
        win_x = (scr_w - win_w) // 2
        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.addstr(2, 3, "Refreshing data...")
        win.border()
        win.refresh()

    def __exit__(self, *_):
        curses.endwin()

def view_runs(get_data_cb):
    with util.LogCapture() as logs:
        Viewer.get_data = staticmethod(get_data_cb)
        Viewer.logs = logs
        tabview.Viewer = Viewer
        tabview.view(
            [[]],
            column_width="max",
            info="Guild run comparison",
        )
