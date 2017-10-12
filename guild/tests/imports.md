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

    >>> expected = [
    ...   'guild.__init__',
    ...   'guild.app',
    ...   'guild.check_cmd',
    ...   'guild.check_cmd_impl',
    ...   'guild.cli',
    ...   'guild.click_util',
    ...   'guild.cmd_support',
    ...   'guild.config',
    ...   'guild.install_cmd',
    ...   'guild.log',
    ...   'guild.main',
    ...   'guild.main_bootstrap',
    ...   'guild.main_cmd',
    ...   'guild.main_cmd_impl',
    ...   'guild.models_cmd',
    ...   'guild.models_cmd_impl',
    ...   'guild.namespace',
    ...   'guild.op',
    ...   'guild.op_main',
    ...   'guild.operations_cmd',
    ...   'guild.operations_cmd_impl',
    ...   'guild.package',
    ...   'guild.packages_cmd',
    ...   'guild.packages_delete_cmd',
    ...   'guild.packages_info_cmd',
    ...   'guild.packages_list_cmd',
    ...   'guild.packages_cmd_impl',
    ...   'guild.pip_util',
    ...   'guild.plugin',
    ...   'guild.plugin_util',
    ...   'guild.plugins.__init__',
    ...   'guild.plugins.cpu',
    ...   'guild.plugins.disk',
    ...   'guild.plugins.gpu',
    ...   'guild.plugins.keras',
    ...   'guild.plugins.memory',
    ...   'guild.plugins.python_util',
    ...   'guild.plugins.tensorflow_util',
    ...   'guild.project',
    ...   'guild.run',
    ...   'guild.run_cmd',
    ...   'guild.run_cmd_impl',
    ...   'guild.runs_cmd',
    ...   'guild.runs_cmd_impl',
    ...   'guild.runs_cmd_support',
    ...   'guild.runs_delete_cmd',
    ...   'guild.runs_info_cmd',
    ...   'guild.runs_list_cmd',
    ...   'guild.runs_restore_cmd',
    ...   'guild.shell_cmd',
    ...   'guild.shell_cmd_impl',
    ...   'guild.tensorboard',
    ...   'guild.test',
    ...   'guild.train_cmd',
    ...   'guild.uninstall_cmd',
    ...   'guild.util',
    ...   'guild.var',
    ...   'guild.view_cmd',
    ...   'guild.view_cmd_impl']
    >>> compare_sets(set(expected), set([m.__name__ for m in iter_mods()]))
    Sets are the same
