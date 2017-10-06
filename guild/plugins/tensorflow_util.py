from __future__ import absolute_import

import logging
import time

from guild.plugin import Plugin
from guild.plugins import python_util

class SummaryPlugin(Plugin):

    MIN_SUMMARY_INTERVAL = 5

    SUMMARY_NAME = None

    def __init__(self):
        self._summary_cache = SummaryCache(self.MIN_SUMMARY_INTERVAL)

    def patch_env(self):
        import tensorflow
        python_util.listen_method(
            tensorflow.summary.FileWriter.add_summary,
            self._handle_summary)

    def _handle_summary(self, add_summary, _summary, step):
        if self._summary_cache.expired():
            self._log(logging.info, "reading %(name)s")
            try:
                vals = self.read_summary_values()
            except:
                logging.exception(
                    "reading %s", self.SUMMARY_NAME or "summary values")
                vals = {}
            self._summary_cache.reset_for_step(step, vals)
        vals = self._summary_cache.for_step(step)
        if vals:
            self._log(logging.debug, "%(name)s: %(vals)s", vals=vals)
            summary = tf_scalar_summary(vals)
            add_summary(summary, step)

    def read_summary_values(self):
        return {}

    def _log(self, f, msg, **kw):
        if self.SUMMARY_NAME:
            args = dict(kw)
            args["name"] = self.SUMMARY_NAME
            f(msg, args)

def tf_scalar_summary(vals):
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
