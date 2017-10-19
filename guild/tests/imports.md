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
    ...   'guild.cmd_impl_support',
    ...   'guild.commands.run',
    ...   'guild.commands.__init__',
    ...   'guild.commands.check',
    ...   'guild.commands.check_impl',
    ...   'guild.commands.help',
    ...   'guild.commands.help_impl',
    ...   'guild.commands.install',
    ...   'guild.commands.main',
    ...   'guild.commands.main_impl',
    ...   'guild.commands.models',
    ...   'guild.commands.models_impl',
    ...   'guild.commands.operations',
    ...   'guild.commands.operations_impl',
    ...   'guild.commands.package',
    ...   'guild.commands.package_impl',
    ...   'guild.commands.packages',
    ...   'guild.commands.packages_impl',
    ...   'guild.commands.packages_delete',
    ...   'guild.commands.packages_info',
    ...   'guild.commands.packages_list',
    ...   'guild.commands.run_impl',
    ...   'guild.commands.runs',
    ...   'guild.commands.runs_impl',
    ...   'guild.commands.runs_support',
    ...   'guild.commands.runs_delete',
    ...   'guild.commands.runs_info',
    ...   'guild.commands.runs_list',
    ...   'guild.commands.runs_purge',
    ...   'guild.commands.runs_restore',
    ...   'guild.commands.shell',
    ...   'guild.commands.shell_impl',
    ...   'guild.commands.tensorflow_info_main',
    ...   'guild.commands.train',
    ...   'guild.commands.uninstall',
    ...   'guild.commands.view',
    ...   'guild.commands.view_impl',
    ...   'guild.config',
    ...   'guild.entry_point_util',
    ...   'guild.help',
    ...   'guild.log',
    ...   'guild.main',
    ...   'guild.main_bootstrap',
    ...   'guild.model',
    ...   'guild.modelfile',
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
    ...   'guild.run',
    ...   'guild.tensorboard',
    ...   'guild.test',
    ...   'guild.util',
    ...   'guild.var']
    >>> compare_sets(set(expected), set([m.__name__ for m in iter_mods()]))
    Sets are the same
