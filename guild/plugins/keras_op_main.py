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

import argparse
import logging
import os
import sys
import time

# Defer import of keras. While this module is only used in ops and we
# could import keras here, we test all our module imports and loading
# keras here will fail in test envs that don't support keras. It's
# also slow, noisy, and side-effecty.

from guild import op_util
from guild import python_util
from guild import util

log = logging.getLogger("guild.keras")

warnings = {}

class Op(object):
    """Abstract Keras operation.
    """

    name = None

    def __init__(self, args):
        self.args, self.script_args = self._parse_args(args)
        self.script = self._find_script()

    def _find_script(self):
        # Look for script in cwd and then CMD_DIR (user's cwd)
        return util.find_apply([
            self._cwd_script,
            self._cmd_dir_script,
            self._no_script_error,
        ])

    def _cwd_script(self):
        path = os.path.join(".", self.args.script)
        if os.path.exists(path):
            return path
        return None

    def _cmd_dir_script(self):
        path = os.path.join(os.environ["CMD_DIR"], self.args.script)
        if os.path.exists(path):
            return path
        return None

    def _no_script_error(self):
        raise SystemExit("cannot find script %s" % self.args.script)

    def _parse_args(self, args):
        p = self._init_arg_parser()
        return p.parse_known_args(args)

    def _init_arg_parser(self):
        assert self.name
        p = argparse.ArgumentParser(usage="keras_op_main.py %s" % self.name)
        p.add_argument("script")
        return p

    def __call__(self):
        python_util.exec_script(self.script, self._global_assigns())

    def _global_assigns(self):
        flags = op_util.args_to_flags(self.script_args)
        return {
            name[6:]: flags[name] for name in flags
            if name[:6] == "const:"
        }

class Run(Op):

    name = "run"

    def __call__(self):
        sys.argv = [self.script] + self._pop_const_args(self.script_args)
        super(Run, self).__call__()

    @staticmethod
    def _pop_const_args(args0):
        args = []
        skip_next = False
        for val in args0:
            if skip_next:
                skip_next = False
                continue
            if val.startswith("--const:"):
                if "=" not in val:
                    skip_next = True
                continue
            args.append(val)
        return args

class Train(Op):

    name = "train"

    def _init_arg_parser(self):
        p = super(Train, self)._init_arg_parser()
        p.add_argument("--epochs", type=int)
        p.add_argument("--batch-size", type=int)
        return p

    def __call__(self):
        patch_keras(self.args.batch_size, self.args.epochs)
        super(Train, self).__call__()

class Predict(Op):

    name = "predict"

_op_types = (Run, Train, Predict)

def patch_keras(batch_size=None, epochs=None):
    import keras
    fit = _fit_wrapper(batch_size, epochs)
    fit_gen = _fit_gen_wrapper(epochs)
    _patch(keras.models.Sequential, "fit", fit)
    _patch(keras.models.Sequential, "fit_generator", fit_gen)
    _patch(keras.models.Model, "fit", fit)
    _patch(keras.models.Model, "fit_generator", fit_gen)
    _patch(keras.callbacks.TensorBoard, "set_params", _set_tensorboard_params)

def _patch(cls, method, wrapper):
    python_util.listen_method(cls, method, wrapper)

def _fit_wrapper(batch_size, epochs):
    def fit(fit0, *args, **kw):
        _maybe_apply_kw("batch_size", batch_size, kw)
        _maybe_apply_kw("epochs", epochs, kw)
        _ensure_tensorboard_callback(kw)
        _ensure_checkpoint_callback(kw)
        raise python_util.Result(fit0(*args, **kw))
    return fit

def _fit_gen_wrapper(epochs):
    def fit_gen(fit_gen0, *args, **kw):
        _maybe_apply_kw("epochs", epochs, kw)
        _ensure_tensorboard_callback(kw)
        _ensure_checkpoint_callback(kw)
        raise python_util.Result(fit_gen0(*args, **kw))
    return fit_gen

def _maybe_apply_kw(name, val, kw):
    if val is not None:
        kw[name] = val

def _ensure_tensorboard_callback(kw):
    import keras
    cb = _ensure_callback(
        keras.callbacks.TensorBoard, kw,
        write_graph=True)
    cb.log_dir = op_util.current_run().path

def _ensure_checkpoint_callback(kw):
    import keras
    try:
        import h5py as _
    except ImportError:
        _warn_missing_h5py()
    else:
        filepath = "weights-{epoch:05d}.h5"
        _ensure_callback(
            keras.callbacks.ModelCheckpoint, kw,
            filepath=filepath)

def _warn_missing_h5py():
    if "h5py" not in warnings:
        log.warning(
            "h5py is not installed - model checkpoints "
            "will be disabled")
        warnings["h5py"] = True

def _ensure_callback(cls, fit_kw, **cb_kw):
    callbacks = fit_kw.setdefault("callbacks", [])
    for cb in callbacks:
        if isinstance(cb, cls):
            break
    else:
        cb = cls(**cb_kw)
        callbacks.append(cb)
    return cb

def _set_tensorboard_params(_sp0, params):
    flags = {
        name: val
        for name, val in params.items()
        if isinstance(val, (str, int, float, bool))
    }
    op_util.current_run().write_attr("flags", flags)

def _init_op(name, op_args):
    for op_type in _op_types:
        if op_type.name == name:
            return op_type(op_args)
    op_util.exit("unrecognized plugin op '%s'" % name)

def main(args):
    op_name, op_args = op_util.parse_op_args(args)
    try:
        import keras as _
    except ImportError:
        op_util.exit("cannot import keras - is it installed?")
    op = _init_op(op_name, op_args)
    try:
        op()
    except KeyboardInterrupt:
        sys.stderr.write("Stopping run\n")
        sys.stderr.flush()
        time.sleep(1) # Hack to let TensorFlow shutdown gracefully
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
