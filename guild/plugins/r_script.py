import os
import os.path
import json
import subprocess


from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import util
from guild import cli


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

        script_data = peek_script_guild_info(self.script_path)

        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": """Rscript -e 'guildai:::run_with_global_flags("%s")' ${flag_args}"""
                        % (os.path.relpath(self.script_path)),
                        "flags-dest": 'globals',
                        "flags": script_data['global-flags'],
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
                                            "**.[rR]",
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


def peek_script_guild_info(r_script_path):
    out = run_r("guildai:::peek_r_script_guild_info('%s')" % r_script_path)
    return json.loads(out)


def is_r_script(opspec):
    return os.path.isfile(opspec) and opspec[-2:].upper() == ".R"


def check_guild_r_package_installled():
    installed = run_r('cat(requireNamespace("guildai", quietly = TRUE))') == "TRUE"
    if installed:
        return

    # TODO, consider vendoring r-pkg as part of pip pkg, auto-bootstrap R install
    # into a stand-alone lib we inject via prefixing R_LIBS env var
    consent = cli.confirm(
        "The 'guildai' R package must be installed in the R library. Continue?", True
    )
    if consent:

        run_r(
            infile="""
        if(!require("remotes", quietly = TRUE))
            utils::install.packages("remotes", repos = c(CRAN = "https://cran.rstudio.com/"))

        install_github("t-kalinowski/guildai-r")
        """
        )

        # Still need to figure out the appropriate home for this r package
        # if we bundle it w/ the python module we could install with something like:
        #   path_r_pkg_src_dir = resolve_using(__path__)
        #   run_r('remotes::install_local("%s")' % path_r_pkg_src_dir)
        # or we could pull from cran directly:
        #  'utils::install.packages("guildai", repos = c(CRAN = "https://cran.rstudio.com/"))'
        #  or install w/o the remotes, but then we'll have to resolve R dep pkgs (e.g., jsonlite) manually first
        # 'utils::install.packages("%s", repos = NULL, type = "source")' % path_to_r_pkg_src

        return

    raise ImportError


def run_r(
    *exprs, file=None, infile=None, vanilla=True, default_packages='base', **run_kwargs
):
    """Run R code in a subprocess, return stderr+stdout output in a single string

    This has different defaults from `Rscript`, designed for isolated, fast invocations.
    Args:
      exprs: strings of individual R expressions to be evaluated sequentially
      file: path to an R script
      infile: multiline string of R code, piped into Rscript frontend via stdin.
    """
    assert (
        sum(map(bool, [exprs, file, infile])) == 1
    ), "exprs, file, and infile, are mutually exclusive. Only supply one."

    cmd = ["Rscript"]
    if default_packages:
        cmd.append("--default-packages=%s" % default_packages)
    if vanilla:
        cmd.append("--vanilla")

    if file:
        cmd.append(file)
    elif exprs:
        for e in exprs:
            cmd.extend(["-e", e])
    elif infile:
        cmd.append("-")
        run_kwargs['input'] = infile.encode()

    run_kwargs.setdefault("stderr", subprocess.STDOUT)
    run_kwargs.setdefault("stdout", subprocess.PIPE)
    run_kwargs.setdefault("check", True)

    out = subprocess.run(cmd, **run_kwargs)
    return out.stdout.decode()
