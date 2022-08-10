import os
import os.path
import json
import subprocess


from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import util


class RScriptModelProxy:
    name = ""
    fullname = ""
    output_scalars = None
    objective = "loss"
    plugins = []

    def __init__(self, script_path, op_name):
        assert script_path[-2:].upper() == ".R", script_path
        assert script_path.endswith(op_name), (script_path, op_name)
        self.script_path = script_path
        if os.path.isabs(op_name) or op_name.startswith(".."):
            self.op_name = os.path.basename(op_name)
        else:
            self.op_name = op_name
        script_base = script_path[: -len(self.op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)
        self.modeldef = self._init_modeldef()

    def _init_modeldef(self):

        flags_data = infer_global_flags(self.script_path)
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": """Rscript -e 'guild.ai:::do_guild_run("%s")' ${flag_args}"""
                        % (os.path.relpath(self.script_path)),
                        "flags-dest": 'globals',
                        "flags": flags_data,
                        # "output-scalars": self.output_scalars,
                        # "objective": self.objective,
                        # "plugins": self.plugins,
                        "sourcecode": {
                            "dest": ".",
                            "select": [
                                {"exclude": {"dir": "renv"}},
                                {
                                    "include": {
                                        "text": [
                                            "renv.lock",
                                            ".Rprofile",
                                            ".Renviron",
                                            "*.[rR]",
                                        ]
                                    }
                                },
                            ],
                        },
                    }
                },
            }
        ]
        gf = guildfile.Guildfile(data, dir=os.path.dirname(self.script_path))
        return gf.models[self.name]


class RScriptPlugin(pluginlib.Plugin):

    resolve_model_op_priority = 60
    # share priority level with python_script, 60
    # must be less than exec_script level of 100

    def resolve_model_op(self, opspec):
        # pylint: disable=unused-argument,no-self-use
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to a model, the function should
        return None.
        """
        if opspec.startswith(("/", "./")) and os.path.isfile(opspec):
            path = opspec
        else:
            path = os.path.join(config.cwd(), opspec)
        if is_r_script(path):
            model = RScriptModelProxy(path, opspec)
            return model, model.op_name
        return None


def normalize_path(x):
    x = os.path.expanduser(x)
    x = os.path.abspath(x)
    return x


def infer_global_flags(r_script_path):

    out = subprocess.run(
        [
            "Rscript",
            "--vanilla",
            "--default-packages=base",
            '-e',
            "guild.ai:::infer_and_emit_global_flags('%s')" % r_script_path,
        ],
        check=True,
        capture_output=True,
    )

    return json.loads(out.stdout.decode())


def is_r_script(opspec):
    return os.path.isfile(opspec) and opspec[-2:].upper() == ".R"


