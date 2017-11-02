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

import os
import shlex
import types

from guild import plugin_util
from guild import plugin
from guild.plugins import python_util

class KerasPlugin(plugin.Plugin):

    def find_models(self, path):
        return python_util.script_models(
            path, self._is_keras_script, self._script_model)

    def _is_keras_script(self, script):
        return self._imports_keras(script) and self._calls_fit_method(script)

    @staticmethod
    def _imports_keras(script):
        return any(
            (name == "keras" or name.startswith("keras.")
             for name in script.imports()))

    @staticmethod
    def _calls_fit_method(script):
        return any((call.name == "fit" for call in script.calls()))

    @staticmethod
    def _script_model(script):
        return {
            "name": script.name,
            "operations": {
                "train": {
                    "cmd": "@keras:train '%s'" % os.path.abspath(script.src),
                    "description": "Train the model",
                }
            }
        }

    def enabled_for_op(self, op):
        parts = shlex.split(op.cmd)
        if parts[0] != "@keras:train":
            return False, "operation not supported by plugin"
        return True, ""

    def run_op(self, op_spec, args):
        if op_spec == "train":
            self._train(args)
        else:
            raise plugin.NotSupported(op_spec)

    def _train(self, op_args):
        try:
            import keras
        except ImportError:
            plugin_util.exit("error: could not import keras - is it installed?")
        parsed_args = self._parse_args(op_args)
        self._patch_keras(parsed_args)
        self._exec_script(parsed_args)

    @staticmethod
    def _parse_args(args):
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("script")
        p.add_argument("--epochs", type=int)
        p.add_argument("--batch-size", type=int)
        p.add_argument("--datasets")
        parsed, _ = p.parse_known_args(args)
        return parsed

    def _patch_keras(self, args):
        import keras
        python_util.listen_method(
            keras.models.Sequential, "fit",
            self._fit_wrapper(args))
        python_util.listen_method(
            keras.callbacks.TensorBoard, "set_params",
            self._on_set_tensorboard_params)
        python_util.listen_function(
            keras.utils.data_utils, "get_file",
            self._get_file_wrapper(args))
        self._update_keras_get_file_refs()

    def _fit_wrapper(self, op_args):
        def fit(fit0, *args, **kw):
            self._maybe_apply_kw("batch_size", op_args.batch_size, kw)
            self._maybe_apply_kw("epochs", op_args.epochs, kw)
            self._ensure_tensorboard_callback(kw)
            raise python_util.Result(fit0(*args, **kw))
        return fit

    @staticmethod
    def _maybe_apply_kw(name, val, kw):
        if val:
            kw[name] = val

    @staticmethod
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

    @staticmethod
    def _on_set_tensorboard_params(_set_params, params):
        run = plugin_util.current_run()
        flags = {
            name: val
            for name, val in params.items()
            if isinstance(val, (str, int, float, bool))
        }
        run.write_attr("flags", flags)

    def _get_file_wrapper(self, op_args):
        def get_file(get_file0, fname, *args, **kw):
            subdir = kw.get("cache_subdir", "datasets")
            if subdir == "datasets" and op_args.datasets:
                fname = os.path.abspath(os.path.join(op_args.datasets, fname))
            self.log.debug("getting file %s", fname)
            raise python_util.Result(get_file0(fname, *args, **kw))
        return get_file

    @staticmethod
    def _update_keras_get_file_refs():
        # Keras actively loads everything on import so referenes to
        # `keras.utils.data_utils.get_file` are all using the
        # unpatched function by the time we're able to patch it. We
        # have to unfortunately traverse the keras package and update
        # those references.
        import keras
        from keras.utils.data_utils import get_file as patched
        assert patched.__wrapper__, patched # pylint: disable=no-member
        ref_spec = (
            "get_file",
            types.FunctionType,
            {"__module__": "keras.utils.data_utils"})
        python_util.update_refs(keras, ref_spec, patched, recurse=True)

    @staticmethod
    def _exec_script(args):
        python_util.exec_script(args.script)
