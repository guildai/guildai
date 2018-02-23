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
import sys

# Defer import of keras. While this module is only used in ops and we
# could import keras here, we test all our module imports and loading
# keras here will fail in test envs that don't support keras. It's
# also slow, noisy, and side-effecty.

from guild import plugin_util
from guild.plugins import python_util

log = logging.getLogger("guild.keras")

class Op(object):
    """Abstract Keras operation.
    """

    name = None

    def __init__(self, args):
        self.args, self.script_parse = self._parse_known_args(args)

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

    @staticmethod
    def _init_run():
        # Cwd is changed to run dir, so we need to replicate the
        # original cwd (CMD_DIR env) with links to each file/dir. This
        # is equivalent to resource resolution in a model-defined
        # operation.
        run = plugin_util.current_run()
        cmd_dir = os.getenv("CMD_DIR")
        assert cmd_dir
        for name in os.listdir(cmd_dir):
            if name == ".guild":
                continue
            src = os.path.join(cmd_dir, name)
            link = os.path.join(run.path, name)
            os.symlink(src, link)

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
        return p

    def _exec_script(self):
        patch_keras(self.args)
        super(Train, self)._exec_script()

class Predict(Op):

    name = "predict"

def patch_keras(args):
    import keras
    fit = _fit_wrapper(args)
    fit_gen = _fit_gen_wrapper(args)
    _patch(keras.models.Sequential, "fit", fit)
    _patch(keras.models.Sequential, "fit_generator", fit_gen)
    _patch(keras.models.Model, "fit", fit)
    _patch(keras.models.Model, "fit_generator", fit_gen)
    _patch(keras.callbacks.TensorBoard, "set_params", _set_tensorboard_params)

def _patch(cls, method, wrapper):
    python_util.listen_method(cls, method, wrapper)

def _fit_wrapper(op_args):
    def fit(fit0, *args, **kw):
        _maybe_apply_kw("batch_size", op_args.batch_size, kw)
        _maybe_apply_kw("epochs", op_args.epochs, kw)
        _ensure_tensorboard_callback(kw)
        raise python_util.Result(fit0(*args, **kw))
    return fit

def _fit_gen_wrapper(op_args):
    def fit_gen(fit_gen0, *args, **kw):
        _maybe_apply_kw("epochs", op_args.epochs, kw)
        _ensure_tensorboard_callback(kw)
        raise python_util.Result(fit_gen0(*args, **kw))
    return fit_gen

def _maybe_apply_kw(name, val, kw):
    if val:
        kw[name] = val

def _ensure_tensorboard_callback(kw):
    import keras
    callbacks = kw.setdefault("callbacks", [])
    for cb in callbacks:
        if isinstance(cb, keras.callbacks.TensorBoard):
            break
    else:
        cb = keras.callbacks.TensorBoard(write_graph=True)
        callbacks.append(cb)
    cb.log_dir = plugin_util.current_run().path

def _set_tensorboard_params(_sp0, params):
    flags = {
        name: val
        for name, val in params.items()
        if isinstance(val, (str, int, float, bool))
    }
    plugin_util.current_run().write_attr("flags", flags)

def _init_op(name, op_args):
    if name == "train":
        return Train(op_args)
    elif name == "predict":
        return Predict(op_args)
    else:
        plugin_util.exit("unrecognized command '%s'" % name)

def main(args):
    op_name, op_args = plugin_util.parse_op_args(args)
    try:
        import keras as _
    except ImportError:
        plugin_util.exit("cannot import keras - is it installed?")
    _init_op(op_name, op_args)()

if __name__ == "__main__":
    main(sys.argv)
