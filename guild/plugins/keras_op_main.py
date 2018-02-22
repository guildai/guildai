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

import argparse
import logging
import os
import types

# Defer import of keras. While this module is only used in ops and we
# could import keras here, we test all our module imports and loading
# keras here will fail in test envs that don't support keras. It's
# also slow, noisy, and side-effecty.

from guild import plugin_util
from guild.plugins import python_util

log = logging.getLogger("guild.keras")

class Op(object):

    name = None

    def __init__(self, args):
        self.args, self.script_parse = self._parse_known_args(args)
        self.run = plugin_util.current_run()

    def _parse_known_args(self, args):
        p = self._init_arg_parser()
        return p.parse_known_args(args)

    def _init_arg_parser(self):
        assert self.name
        p = argparse.ArgumentParser(usage="keras_op_main.py %s" % self.name)
        p.add_argument("script")
        return p

    def __call__(self):
        self._init_run()
        self._exec_script()

    def _init_run(self):
        # Cwd is changed to rundir, so we need to replicate the
        # original cwd (CMD_DIR env) with links to each file/dir
        cmd_dir = os.getenv("CMD_DIR")
        assert cmd_dir
        for name in os.listdir(cmd_dir):
            if name == ".guild":
                continue
            src = os.path.join(cmd_dir, name)
            link = os.path.join(self.run.path, name)
            os.symlink(src, link)

    @staticmethod
    def _patch_env():
        pass

    def _exec_script(self):
        # Execute the script as code rather than import it because we
        # insert the Keras tensorflow callback, which starts
        # background threads - this will cause import to hang.
        python_util.exec_script(self.args.script)

class Train(Op):

    name = "train"

    def _init_arg_parser(self):
        p = super(Train, self)._init_arg_parser()
        p.add_argument("--epochs", type=int)
        p.add_argument("--batch-size", type=int)
        p.add_argument("--datasets")
        return p

    def _exec_script(self):
        self._patch_keras()
        super(Train, self)._exec_script()

    def _patch_keras(self):
        import keras
        python_util.listen_method(
            keras.models.Sequential, "fit",
            self._fit_wrapper())
        python_util.listen_method(
            keras.callbacks.TensorBoard, "set_params",
            self._on_set_tensorboard_params)
        python_util.listen_function(
            keras.utils.data_utils, "get_file",
            self._get_file_wrapper())
        self._update_keras_get_file_refs()

    def _fit_wrapper(self):
        def fit(fit0, *args, **kw):
            _maybe_apply_kw("batch_size", self.args.batch_size, kw)
            _maybe_apply_kw("epochs", self.args.epochs, kw)
            self._ensure_tensorboard_callback(kw)
            raise python_util.Result(fit0(*args, **kw))
        return fit

    def _ensure_tensorboard_callback(self, kw):
        import keras
        callbacks = kw.setdefault("callbacks", [])
        for cb in callbacks:
            if isinstance(cb, keras.callbacks.TensorBoard):
                break
        else:
            cb = keras.callbacks.TensorBoard(write_graph=True)
            callbacks.append(cb)
        cb.log_dir = self.run.path

    def _on_set_tensorboard_params(self, _set_params, params):
        flags = {
            name: val
            for name, val in params.items()
            if isinstance(val, (str, int, float, bool))
        }
        self.run.write_attr("flags", flags)

    def _get_file_wrapper(self):
        def get_file(get_file0, fname, *args, **kw):
            subdir = kw.get("cache_subdir", "datasets")
            if subdir == "datasets" and self.args.datasets:
                fname = os.path.abspath(os.path.join(self.args.datasets, fname))
            log.debug("getting file %s", fname)
            raise python_util.Result(get_file0(fname, *args, **kw))
        return get_file

    @staticmethod
    def _update_keras_get_file_refs():
        # Keras actively loads everything on import so referenes to
        # `keras.utils.data_utils.get_file` are all using the
        # unpatched function by the time we're able to patch it. We
        # have to unfortunately traverse the entire keras package and update
        # those references.
        import keras
        from keras.utils.data_utils import get_file as patched
        assert patched.__wrapper__, patched
        ref_spec = (
            "get_file",
            types.FunctionType,
            {"__module__": "keras.utils.data_utils"})
        python_util.update_refs(keras, ref_spec, patched, recurse=True)

class Predict(Op):

    name = "predict"

def _maybe_apply_kw(name, val, kw):
    if val:
        kw[name] = val

def _init_op(name, op_args):
    if name == "train":
        return Train(op_args)
    elif name == "predict":
        return Predict(op_args)
    else:
        plugin_util.exit("unrecognized command '%s'" % name)

if __name__ == "__main__":
    op_name, op_args = plugin_util.parse_op_args()
    _init_op(op_name, op_args)()
