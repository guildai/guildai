import os


from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import util


def is_r_script(opspec):
    return os.path.isfile(opspec) and opspec[-2:].upper() == ".R"


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

        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": "Rscript %s ${flag_args}" % self.script_path,
                        # "flags": flags_data,
                        # "flags-dest": flags_dest,
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
        print("resolve_model_op() called")
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


