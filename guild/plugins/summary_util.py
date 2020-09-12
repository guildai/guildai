# Copyright 2017-2020 TensorHub, Inc.
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
import warnings

from guild import python_util
from guild import util

from guild.plugin import Plugin


class SummaryPlugin(Plugin):
    """Summary plugin base class.

    Summary plugins log additional summary values (e.g. GPU usage,
    etc.) per logged summary. This class is used to patch the TF env
    to handle `add_summary` of `tensorflow.summary.FileWriter` and of
    `tensorboardX.writer.SummaryToEventTransformer`.
    """

    provides = Plugin.provides + ["all", "summary"]

    MIN_SUMMARY_INTERVAL = 5

    def __init__(self, ep):
        super(SummaryPlugin, self).__init__(ep)
        self._summary_cache = SummaryCache(self.MIN_SUMMARY_INTERVAL)

    def patch_env(self):
        self.log.debug("patching tensorflow")
        self._patch_guild_summary()
        self._try_patch_tensorboardX()
        self._try_patch_tensorflow()

    def _patch_guild_summary(self):
        from guild import summary

        python_util.listen_method(
            summary.SummaryWriter, "add_scalar", self._handle_guild_scalar
        )

    def _try_patch_tensorboardX(self):
        try:
            from tensorboardX import SummaryWriter
        except ImportError:
            pass
        else:
            self.log.debug("wrapping tensorboardX.SummaryWriter.add_scalar")
            python_util.listen_method(SummaryWriter, "add_scalar", self._handle_scalar)

    def _try_patch_tensorflow(self):
        try:
            import tensorflow as _
        except ImportError:
            pass
        else:
            util.try_apply(
                [
                    self._try_listen_tf_v2,
                    self._try_listen_tf_v1,
                    self._try_listen_tf_legacy,
                    self._listen_tf_failed,
                ]
            )

    def _try_listen_tf_v2(self):
        if not _tf_version().startswith("2."):
            raise util.TryFailed()
        self._listen_tb_v2_summary()
        self._listen_tf_v2_summary()
        self._listen_tf_summary()

    def _listen_tb_v2_summary(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Warning)
            from tensorboard.plugins.scalar import summary_v2
        self.log.debug("wrapping tensorboard.plugins.scalar.summary_v2.scalar")
        python_util.listen_function(summary_v2, "scalar", self._handle_scalar)

    def _listen_tf_v2_summary(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Warning)
            # pylint: disable=import-error,no-name-in-module
            from tensorflow.python.ops import summary_ops_v2
        self.log.debug("wrapping tensorflow.python.ops summary_ops_v2.scalar")
        python_util.listen_function(
            summary_ops_v2, "scalar", self._handle_scalar_ops_v2
        )

    def _listen_tf_summary(self):
        # pylint: disable=import-error,no-name-in-module
        from tensorflow import summary

        self.log.debug("wrapping tensorflow.summary.scalar")
        python_util.listen_function(summary, "scalar", self._handle_scalar)

    def _try_listen_tf_v1(self):
        if not _tf_version().startswith("1."):
            raise util.TryFailed()
        try:
            # pylint: disable=import-error,no-name-in-module
            from tensorflow.compat.v1.summary import FileWriter
        except Exception as e:
            self.log.debug(
                "error importing tensorflow.compat.v1.summary.FileWriter: %s", e
            )
            raise util.TryFailed()
        else:
            self.log.debug(
                "wrapping tensorflow.compat.v1.summary.FileWriter.add_summary"
            )
            python_util.listen_method(FileWriter, "add_summary", self._handle_summary)

    def _try_listen_tf_legacy(self):
        if not _tf_version().startswith("1."):
            raise util.TryFailed()
        try:
            # pylint: disable=import-error,no-name-in-module
            from tensorflow.summary import FileWriter
        except Exception as e:
            self.log.debug("error importing tensorflow.summary.FileWriter: %s", e)
            raise util.TryFailed()
        else:
            self.log.debug("wrapping tensorflow.summary.FileWriter.add_summary")
            python_util.listen_method(FileWriter, "add_summary", self._handle_summary)

    def _listen_tf_failed(self):
        self.log.warning(
            "unable to find TensorFlow summary writer, skipping " "summaries for %s",
            self.name,
        )

    def _handle_guild_scalar(self, add_scalar, _tag, _value, step=None):
        """Handler for guild.summary.SummaryWriter.add_scalar."""
        vals = self._summary_values(step)
        if vals:
            self.log.debug("summary values via add_scalar: %s", vals)
            for tag, val in vals.items():
                if val is not None:
                    add_scalar(tag, val, step)

    def _handle_summary(self, add_summary, _summary, global_step=None):
        """Callback to apply summary values via add_summary callback.

        This is the TF 1.x API for logging scalars.

        See SummaryPlugin docstring above for background.
        """
        vals = self._summary_values(global_step)
        if vals:
            self.log.debug("summary values via add_summary: %s", vals)
            summary = tf_scalar_summary(vals)
            add_summary(summary, global_step)

    def _summary_values(self, global_step):
        if self._summary_cache.expired():
            self.log.debug("reading summary values")
            try:
                vals = self.read_summary_values(global_step)
            except:
                self.log.exception("reading summary values")
                vals = {}
            self._summary_cache.reset_for_step(global_step, vals)
        return self._summary_cache.for_step(global_step)

    def _handle_scalar(self, scalar, _name, _data, step=None, description=None):
        """Callback to apply summary values via scalars API.

        This is the TF 2.x and tensorboardX API for logging scalars.
        """
        # pylint: disable=unused-argument
        vals = self._summary_values(step)
        if vals:
            self.log.debug("summary values via scalar: %s", vals)
            for tag, val in vals.items():
                if val is None:
                    continue
                scalar(tag, val, step)

    def _handle_scalar_ops_v2(self, scalar, _name, _tensor, family=None, step=None):
        """Callback to apply summary values from summary_ops_v2."""
        # pylint: disable=unused-argument
        vals = self._summary_values(step)
        if vals:
            self.log.debug("summary values via scalar: %s", vals)
            for tag, val in vals.items():
                if val is None:
                    continue
                scalar(tag, val, step=step)

    @staticmethod
    def read_summary_values(_global_step):
        """Overridden by subclasses."""
        return {}


def _tf_version():
    try:
        import tensorflow
    except ImportError:
        return ""
    else:
        return tensorflow.__version__


def tf_scalar_summary(vals):
    # pylint: disable=import-error,no-name-in-module
    from tensorflow.core.framework.summary_pb2 import Summary

    return Summary(
        value=[Summary.Value(tag=key, simple_value=val) for key, val in vals.items()]
    )


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
