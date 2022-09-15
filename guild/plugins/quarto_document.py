from distutils.log import warn
import os
import os.path
import yaml

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib


class QuartoDocumentModelProxy:
    name = ""
    fullname = ""
    output_scalars = None
    objective = "loss"
    plugins = []

    def __init__(self, script_path, op_name):
        assert script_path[-4:].lower() == ".qmd", script_path
        assert script_path.endswith(op_name), (script_path, op_name)
        self.script_path = script_path
        if os.path.isabs(op_name) or op_name.startswith(".."):
            self.op_name = os.path.basename(op_name)
        else:
            self.op_name = op_name
        script_base = script_path[: -len(self.op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)
        self.modeldef = self._init_modeldef()
        _apply_config_flags(self.modeldef, self.op_name)

    def _init_modeldef(self):
        # TODO: do file paths needs to be quoted for the shell?
        qmd_path = os.path.relpath(self.script_path)
        assert qmd_path.endswith(".qmd")
        op_data = get_qmd_frontmatter(qmd_path)

        op_data["sourcecode"] = {"dest": "."}
        op_data["exec"] = f"quarto render {qmd_path}"

        if "params" in op_data:
            op_data["flags"] = op_data.pop("params")
            params_yml_path = qmd_path[:-4] + "-flags.yml"
            op_data["flags-dest"] = f"config:{params_yml_path}"
            op_data["exec"] += f" --execute-params {params_yml_path}"

        ## TODO: add scalar-outputs support.
        ## 2 approaches:
        ## - write lua quarto filter that extracts stdout from render ast,
        ##   tee/print in to actual stdout or somewhere where the guild parsers sees it.
        ##   Invoke from the exec call like:
        ##     quarto render foo.qmd --lua-filter extract-scalar-ouputs.lua
        ## - make quarto render a json, like:
        ##      quarto render foo.qmd --to all,json
        ##    make guild go into the json post run and then be aware of how
        ##    to extract cell-output-stdout divs from the rendered json.
        ## - maybe call out to a subprocess to
        ##    f"quarto inspect {qmd_path}" for additional info?

        op_data["exec"] += " --to all,json"

        # lua_filter_path = get_quarto_filter("extract-scalar-outputs")
        # op_data["exec"] += f" --lua-filter {lua_filter_path}"

        data = [
            {
                "model": self.name,
                "operations": {self.op_name: op_data},
            }
        ]

        gf = guildfile.Guildfile(data, dir=os.getcwd())  # dir = GUILD_PROJECT
        return gf.models[self.name]


def _apply_config_flags(modeldef, op_name):
    from . import config_flags

    opdef = modeldef.get_operation(op_name)
    config_flags.apply_config_flags(opdef)


class QuartoDocumentPlugin(pluginlib.Plugin):

    resolve_model_op_priority = 60
    # share priority level with python_script, 60
    # must be less than exec_script level of 100

    def resolve_model_op(self, opspec):
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to a model, the function should
        return None.
        """
        # import debugpy; debugpy.breakpoint()
        if opspec.startswith(("/", "./")) and os.path.isfile(opspec):
            path = opspec
        else:
            path = os.path.join(config.cwd(), opspec)
        if is_quarto_document(path):
            model = QuartoDocumentModelProxy(path, opspec)
            return model, model.op_name
        return None


def get_qmd_frontmatter(path):
    data = []
    with open(path) as f:
        line = f.readline().rstrip()
        assert line == "---", "qmd document must start with '---' on first line"
        for line in f:
            if line.rstrip() == "---":
                break
            data.append(line)

        if line.rstrip() != "---":
            warn("qmd missing closing delimmiter for document frontmatter")

        return yaml.safe_load("".join(data))


def normalize_path(x):
    x = os.path.expanduser(x)
    x = os.path.abspath(x)
    return x


def is_quarto_document(opspec):
    return os.path.isfile(opspec) and opspec[-4:] == ".qmd"
