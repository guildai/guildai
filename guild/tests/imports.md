# Imports

    >>> import importlib
    >>> import os
    >>> import guild

    >>> def iter_mods():
    ...   guild_root = os.path.dirname(guild.__file__)
    ...   for root, dirs, files in os.walk(guild_root, topdown=True):
    ...     if "tests" in dirs:
    ...       dirs.remove("tests")
    ...     if "external" in dirs:
    ...       dirs.remove("external")
    ...     for name in files:
    ...       if name.endswith(".py"):
    ...         mod_path = os.path.join(root, name)
    ...         mod_relpath = os.path.relpath(mod_path, guild_root)
    ...         mod_name = "guild." + mod_relpath.replace(os.path.sep, ".")[:-3]
    ...         yield importlib.import_module(mod_name)

    >>> pprint(sorted([m.__name__ for m in iter_mods()]))
    ['guild.__init__',
     'guild.app',
     'guild.check_cmd',
     'guild.cli',
     'guild.cmd_support',
     'guild.config',
     'guild.install_cmd',
     'guild.log',
     'guild.main',
     'guild.main_bootstrap',
     'guild.models_cmd',
     'guild.op',
     'guild.op_main',
     'guild.operations_cmd',
     'guild.packages_cmd',
     'guild.pip_util',
     'guild.plugin',
     'guild.plugins.__init__',
     'guild.plugins.cpu',
     'guild.plugins.disk',
     'guild.plugins.gpu',
     'guild.plugins.keras',
     'guild.plugins.memory',
     'guild.plugins.python_util',
     'guild.plugins.tensorflow_util',
     'guild.project',
     'guild.run',
     'guild.run_cmd',
     'guild.runs_cmd',
     'guild.shell_cmd',
     'guild.sources_cmd',
     'guild.tensorboard',
     'guild.test',
     'guild.util',
     'guild.var',
     'guild.view_cmd']
