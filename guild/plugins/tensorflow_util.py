# Copyright 2017-2018 TensorHub, Inc.
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

import time

from guild import python_util
from guild.plugin import Plugin

class SummaryPlugin(Plugin):

    MIN_SUMMARY_INTERVAL = 5

    def __init__(self, ep):
        super(SummaryPlugin, self).__init__(ep)
        self._summary_cache = SummaryCache(self.MIN_SUMMARY_INTERVAL)

    def patch_env(self):
        # pylint: disable=import-error
        import tensorflow
        self.log.debug("wrapping tensorflow.summary.FileWriter.add_summary")
        python_util.listen_method(
            tensorflow.summary.FileWriter, "add_summary",
            self._handle_summary)

    def _handle_summary(self, add_summary, _summary, step):
        if self._summary_cache.expired():
            self.log.debug("reading summary values")
            try:
                vals = self.read_summary_values(step)
            except:
                self.log.exception("reading summary values")
                vals = {}
            self._summary_cache.reset_for_step(step, vals)
        vals = self._summary_cache.for_step(step)
        if vals:
            self.log.debug("summary values: %s", vals)
            summary = tf_scalar_summary(vals)
            add_summary(summary, step)

    @staticmethod
    def read_summary_values(_step):
        return {}

def tf_scalar_summary(vals):
    # pylint: disable=import-error,no-name-in-module
    from tensorflow.core.framework.summary_pb2 import Summary
    return Summary(value=[
        Summary.Value(tag=key, simple_value=val)
        for key, val in vals.items()
    ])

class SummaryCache(object):

    def __init__(self, timeout):
        self._timeout = timeout
        self._expires = None
        self._step = None
        self._val = None

    def expired(self):
        return self._expires is None or time.time() >= self._expires

    def reset_for_step(self, step, val):
        self._expires = time.time() + self._timeout
        self._step = step
        self._val = val

    def for_step(self, step):
        return self._val if step == self._step else None
