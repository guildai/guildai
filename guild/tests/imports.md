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
    ...   'guild.cli',
    ...   'guild.click_util',
    ...   'guild.cmd_support',
    ...   'guild.commands.run_cmd',
    ...   'guild.commands.__init__',
    ...   'guild.commands.check_cmd',
    ...   'guild.commands.check_cmd_impl',
    ...   'guild.commands.install_cmd',
    ...   'guild.commands.main_cmd',
    ...   'guild.commands.main_cmd_impl',
    ...   'guild.commands.models_cmd',
    ...   'guild.commands.models_cmd_impl',
    ...   'guild.commands.operations_cmd',
    ...   'guild.commands.operations_cmd_impl',
    ...   'guild.commands.package_cmd',
    ...   'guild.commands.package_cmd_impl',
    ...   'guild.commands.packages_cmd',
    ...   'guild.commands.packages_cmd_impl',
    ...   'guild.commands.packages_delete_cmd',
    ...   'guild.commands.packages_info_cmd',
    ...   'guild.commands.packages_list_cmd',
    ...   'guild.commands.run_cmd_impl',
    ...   'guild.commands.runs_cmd',
    ...   'guild.commands.runs_cmd_impl',
    ...   'guild.commands.runs_cmd_support',
    ...   'guild.commands.runs_delete_cmd',
    ...   'guild.commands.runs_info_cmd',
    ...   'guild.commands.runs_list_cmd',
    ...   'guild.commands.runs_restore_cmd',
    ...   'guild.commands.shell_cmd',
    ...   'guild.commands.shell_cmd_impl',
    ...   'guild.commands.tensorflow_info_main',
    ...   'guild.commands.train_cmd',
    ...   'guild.commands.uninstall_cmd',
    ...   'guild.commands.view_cmd',
    ...   'guild.commands.view_cmd_impl',
    ...   'guild.config',
    ...   'guild.log',
    ...   'guild.main',
    ...   'guild.main_bootstrap',
    ...   'guild.namespace',
    ...   'guild.op',
    ...   'guild.op_main',
    ...   'guild.package',
    ...   'guild.package_main',
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
    ...   'guild.tensorboard',
    ...   'guild.test',
    ...   'guild.util',
    ...   'guild.var']
    >>> compare_sets(set(expected), set([m.__name__ for m in iter_mods()]))
    Sets are the same
