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

import curses
import logging

from tabview import tabview

ViewerBase = tabview.Viewer

viewer_help = """
F1 or ?                  Show this help
s                        Sort by current column (ascending)
S                        Sort by current column (descending)
1                        Sort numerically by current column (ascending)
! or 2                   Sort numerically by current column (descending)
a                        Reset sort order
A                        Reset sort order (reversed)
r                        Reload file/data (resets sort order)
{{actions}}
Cursor keys or h,j,k,l   Move highlighted cell
Q or q                   Quit
Home, 0, ^, C-a          Move to start of the current line
End, $, C-e              Move to end of the current line
[num]|                   Move to column <num> (defaults to first column)
PgUp/PgDn or J/K         Move a page up or down
H,L                      Page left or right
g                        Move to top of current column
[num]G                   Move to line <num> (defaults to last line)
Insert or m              Memorize current position
Delete or '              Move to last memorized position
Enter                    View current cell details
/                        Specify a search term
n                        Move to next search result
p                        Move to previous search result
< >                      Decrease / increase column width (all columns)
, .                      Decrease / increase column width (current column)
- +                      Decrease / increase column gap
`                        Show logs (used for troubleshooting issues)
[num]c                   Toggle variable column width mode or set width to [num]
[num]C                   Maximize current column or set width to [num]
[num][                   Skip to [num]th change in row value (backward)
[num]]                   Skip to [num]th change in row value (forward)
[num]{                   Skip to [num]th change in column value (backward)
[num]}                   Skip to [num]th change in column value (forward)
"""

viewer_help_key_width = 25

class Viewer(ViewerBase):

    get_data = None
    get_detail = None
    actions = None

    max_header_width = 12
    max_data_width = 20

    def __init__(self, *args, **kw):
        assert self.get_data is not None
        assert self.get_detail is not None
        with StatusWin("Reading data"):
            data, logs = self._init_data()
        self.logs = logs
        args = (args[0], data) + args[2:]
        kw["column_widths"] = self._column_widths(data)
        # pylint: disable=non-parent-init-called
        ViewerBase.__init__(self, *args, **kw)

    def _init_data(self):
        data, logs = self.get_data()
        return tabview.process_data(data), logs

    def _column_widths(self, data):
        if not data:
            return None
        widths = {}
        self._update_column_widths(widths, data[0], self.max_header_width)
        for row in data[1:]:
            self._update_column_widths(widths, row, self.max_data_width)
        return [widths[col] for col in sorted(widths)]

    @staticmethod
    def _update_column_widths(widths, vals, max_width):
        for col, val in zip(range(len(vals)), vals):
            widths[col] = min(max(len(val), widths.get(col, 0)), max_width)

    def location_string(self, yp, xp):
        lstr = ViewerBase.location_string(self, yp, xp)
        return lstr.replace("-,", "")

    def define_keys(self):
        ViewerBase.define_keys(self)
        del self.keys["t"]
        del self.keys["y"]
        del self.keys[tabview.KEY_CTRL('g')]
        self.keys["1"] = self.sort_by_column_numeric
        self.keys["!"] = self.sort_by_column_numeric_reverse
        self.keys["2"] = self.sort_by_column_numeric_reverse
        self.keys["`"] = self.show_logs
        self.keys.update({
            key: self._action_handler(action_cb)
            for (key, _), action_cb in self.actions
        })

    def show_logs(self):
        self.text_box(self._format_logs(), "Logs")

    def text_box(self, contents, title):
        tabview.TextBox(self.scr, data=contents, title=title)()
        self.resize()

    def _format_logs(self):
        logs = self.logs or []
        fmt = logging.Formatter("%(asctime)s: %(levelname)s %(message)s")
        return "\n".join([fmt.format(r) for r in logs])

    def _action_handler(self, action_cb):
        return lambda: action_cb(self)

    def help(self):
        help_text = self._insert_actions_help(viewer_help.strip())
        tabview.TextBox(self.scr, help_text, "Key bindings")()
        self.resize()

    def _insert_actions_help(self, text):
        actions_help = "\n".join([
            key.ljust(viewer_help_key_width) + help_text
            for (key, help_text), _ in self.actions
        ])
        if actions_help:
            actions_help += "\n"
        return text.replace("{{actions}}\n", actions_help)

    def sort_by_column_numeric(self):
        from operator import itemgetter
        xp = self.x + self.win_x
        self.data = sorted(
            self.data,
            key=lambda x: self.float_key(itemgetter(xp)(x), float('inf')))

    def sort_by_column_numeric_reverse(self):
        from operator import itemgetter
        xp = self.x + self.win_x
        self.data = sorted(
            self.data,
            key=lambda x: self.float_key(itemgetter(xp)(x), float('-inf')),
            reverse=True)

    @staticmethod
    def float_key(value, default):
        try:
            return float(value)
        except ValueError:
            return default

    def show_cell(self):
        yp = self.y + self.win_y
        xp = self.x + self.win_x
        detail = self.get_detail(self.data, yp, xp)
        if not detail:
            return
        content, title = detail
        tabview.TextBox(self.scr, content, title)()
        self.resize()

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

def view_runs(get_data_cb, get_detail_cb, actions):
    Viewer.get_data = staticmethod(get_data_cb)
    Viewer.get_detail = staticmethod(get_detail_cb)
    Viewer.actions = actions
    tabview.Viewer = Viewer
    tabview.view(
        [[]],
        column_width="max",
        info="Guild run comparison",
    )
