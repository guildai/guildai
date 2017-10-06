import os

from guild.plugin import Plugin
from guild.plugins import python_util

class KerasPlugin(Plugin):

    def models_for_location(self, path):
        return python_util.script_models(
            path, _is_keras_script, _script_model)

    def enabled_for_op(self, op):
        return op.cmd == "@keras:train"

    def run_op(self, name, args):
        if name == "train":
            _train(args)
        else:
            raise NotImplementedError(name)

def _is_keras_script(script):
    return _imports_keras(script) and _calls_fit_method(script)

def _imports_keras(script):
    return any(
        (name == "keras" or name.startswith("keras.")
         for name in script.imports()))

def _calls_fit_method(script):
    return any((call.name == "fit" for call in script.calls()))

def _script_model(script):
    return {
        "name": script.name,
        "operations": {
            "train": {
                "cmd": "@keras:train \"%s\"" % script.src,
                "description": "Train the model",
            }
        }
    }

def _train(args):
    print("TODO: train a keras model", args)
    print("*****", os.getenv("RUNDIR"))
