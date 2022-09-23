import os
import os.path
import subprocess
import yaml


from guild import cli
from guild import config
from guild import model as modellib
from guild import model_proxy
from guild import plugin as pluginlib
from guild import r_util


class RScriptModelProxy:
    name = ""
    fullname = ""
    output_scalars = None
    objective = "loss"
    plugins = []

    def __init__(self, script_path, op_name):
        assert script_path[-2:].upper() == ".R", script_path
        assert script_path.endswith(op_name), (script_path, op_name)
        _ensure_guildai_r_package_installled()
        self.script_path = script_path
        if os.path.isabs(op_name) or op_name.startswith(".."):
            self.op_name = os.path.basename(op_name)
        else:
            self.op_name = op_name
        script_base = script_path[: -len(self.op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)
        self.modeldef = _init_modeldef(self.script_path, self.op_name, self.name)
        _apply_config_flags(self.modeldef, self.op_name)


def _init_modeldef(script_path, op_name, model_name):
    op_data = _get_script_guild_data(os.path.relpath(script_path))
    # TODO: instead of using dir=os.getcwd(), consider
    #   - here::here(), or
    #   - os.path.dirname(self.script_path)
    #   - or similar
    return model_proxy.modeldef_for_data(model_name, operations={op_name: op_data})


def _apply_config_flags(modeldef, op_name):
    from . import config_flags

    opdef = modeldef.get_operation(op_name)
    config_flags.apply_config_flags(opdef)


class RScriptPlugin(pluginlib.Plugin):

    resolve_model_op_priority = 60
    # share priority level with python_script, 60
    # must be less than exec_script level of 100

    def resolve_model_op(self, opspec):
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to a model, the function should
        return None.
        """
        if opspec.startswith(("/", "./")) and os.path.isfile(opspec):
            path = opspec
        else:
            path = os.path.join(config.cwd(), opspec)
        if not r_util.is_r_script(path):
            return None
        model = RScriptModelProxy(path, opspec)
        return model, model.op_name


def _get_script_guild_data(r_script_path):
    out = run_r(f"guildai:::emit_r_script_guild_data('{r_script_path}')")
    return yaml.safe_load(out)


def _ensure_guildai_r_package_installled(version="0.0.0.9000"):
    expr = (
        'cat(requireNamespace("guildai", quietly = TRUE) &&'
        f' getNamespaceVersion("guildai") > "{version}")'
    )

    installed = run_r(expr) == "TRUE"
    if installed:
        return

    # TODO, consider vendoring r-pkg as part of pip pkg,
    # auto-bootstrap R install into a stand-alone lib we inject via
    # prefixing R_LIBS env var

    # TODO - we can't interact with the user here. Guild does not
    # typically work this way, altering behavior based on user-input,
    # unless that interaction is implemented in a command impl (this
    # should be consistent across the code base - if there are
    # exceptions that don't arise directly or indirectly from a
    # command impl that's a design flaw/bug).
    #
    # We should look to extend the model def itself to include a set
    # of checks to the env, any of which may query 'user input' (this
    # could be a default answer for non-tty scenarios). Short of that,
    # we should fail here with instructions rather than take action to
    # modify the system.

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
        #  or install w/o the remotes, but then we'll have to resolve
        #  R dep pkgs (e.g., jsonlite) manually first
        # 'utils::install.packages("%s", repos = NULL, type = "source")' % path_to_r_pkg_src

        return

    raise Exception("R is not available")


def run_r(
    *exprs,
    file=None,
    infile=None,
    vanilla=True,
    default_packages='base',
    **run_kwargs,
):
    """Run R code in a subprocess, return stderr+stdout output in a single string.

    This has different defaults from `Rscript`, designed for isolated,
    fast invocations.

    Args:
      `exprs`: strings of individual R expressions to be evaluated sequentially
      `file`: path to an R script
      `infile`: multiline string of R code, piped into Rscript frontend via stdin.

    """
    assert (
        sum(map(bool, [exprs, file, infile])) == 1
    ), "exprs, file, and infile, are mutually exclusive. Only supply one."

    cmd = ["Rscript"]
    if default_packages:
        cmd.append(f"--default-packages={default_packages}")
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

    out = subprocess.run(cmd, check=True, **run_kwargs)
    return out.stdout.decode()


def merge_dicts(dict1, dict2):
    """Recursively merges dict2 into dict1. Modifies dict1 in place"""
    for k in dict2:
        if k in dict1:
            dict1[k] = merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]
    return dict1
