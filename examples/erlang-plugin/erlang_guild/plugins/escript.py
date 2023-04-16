import os

import yaml

from guild import config as configlib
from guild import model as modellib
from guild import model_proxy
from guild import plugin as pluginlib


class EScriptModelProxy:
    def __init__(self, script_path):
        script_dir, script_name = os.path.split(script_path)
        self.name = ""
        self.script_name = script_name
        script_config = _config_for_script(script_path)
        flagdefs = _flags_for_config(script_config)
        exec_args = _exec_args_for_config(script_config)
        exec_spec = _exec_spec(script_name, exec_args)
        self.modeldef = model_proxy.modeldef_for_data(
            script_dir,
            operations={
                script_name: {
                    "exec": exec_spec,
                    "sourcecode": {
                        "dest": "."
                    },
                    "flags": flagdefs,
                },
            },
        )
        self.reference = modellib.script_model_ref("", script_dir)


def _config_for_script(script_path):
    front_matter = _front_matter_for_file(script_path)
    return yaml.safe_load(front_matter)


def _front_matter_for_file(path):
    front_matter = []
    reading = False
    with open(path) as f:
        for line in f.readlines():
            if line.startswith("%%| "):
                reading = True
                front_matter.append(line[4:])
            else:
                if reading:
                    break
    return "".join(front_matter)


def _flags_for_config(config):
    return config.get("flags", {})


def _exec_args_for_config(config):
    return config.get("args", None)


def _exec_spec(script_name, exec_args):
    spec = f"escript {script_name}"
    if exec_args:
        spec = f"{spec} {exec_args}"
    return spec


class EScriptPlugin(pluginlib.Plugin):
    def resolve_model_op(self, opspec):
        path = os.path.join(configlib.cwd(), opspec)
        if _is_erlang_module(path):
            return _model_op_for_module(path)
        return None


def _is_erlang_module(path):
    return os.path.isfile(path) and path.endswith(".erl")


def _model_op_for_module(path):
    model = EScriptModelProxy(path)
    return model, model.script_name
