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

from tabview import tabview

ViewerBase = tabview.Viewer

class Viewer(ViewerBase):

    get_data = None

    def __init__(self, *args, **kw):
        assert self.get_data is not None
        args = (args[0], self._init_data()) + args[2:]
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

def view_runs(get_data_cb):
    Viewer.get_data = staticmethod(get_data_cb)
    tabview.Viewer = Viewer
    tabview.view(
        [[]],
        column_width="max",
        info="Guild run comparison",
    )
