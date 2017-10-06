from guild.plugin import Plugin
from guild.plugins import python_util

class KerasPlugin(Plugin):

    def models_for_location(self, path):
        for script in _keras_scripts(path):
            yield _script_model(script)

def _keras_scripts(path):
    for script in python_util.scripts_for_location(path):
        if _is_keras_script(script):
            yield script

def _is_keras_script(script):
    return _imports_keras(script) and _calls_fit_method(script)

def _imports_keras(script):
    return any(
        (lambda name: name == "keras" or name.startswith("keras.")
         for name in script.imports()))

def _calls_fit_method(script):
    return any(
        (lambda method: call.name == "fit"
         for method in script.calls()))

def _script_model(script):
    return {
        "name": script.name,
    }
