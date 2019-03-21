# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

## Enumerating plugins

Plugins can be registered by installing packages that provide entry
points for the "guild.plugins" group. For these tests, we want to
ensure we are only working with built-ins:

    >>> guild.plugin.limit_to_builtin()

Use `iter_plugins` to iterate through the list of available plugins:

    >>> sorted(guild.plugin.iter_plugins())
    [('cpu', <guild.plugins.cpu.CPUPlugin ...>),
     ('disk', <guild.plugins.disk.DiskPlugin ...>),
     ('exec_script', <guild.plugins.exec_script.ExecScriptPlugin ...>),
     ('gpu', <guild.plugins.gpu.GPUPlugin ...>),
     ('keras', <guild.plugins.keras.KerasPlugin ...>),
     ('memory', <guild.plugins.memory.MemoryPlugin ...>),
     ('perf', <guild.plugins.perf.PerfPlugin ...>),
     ('python_script', <guild.plugins.python_script.PythonScriptPlugin ...>),
     ('skopt', <guild.plugins.skopt.SkoptPlugin ...>)]

## Plugin instances

You can get the plugin instance using `for_name`:

    >>> guild.plugin.for_name("gpu")
    <guild.plugins.gpu.GPUPlugin object ...>

There is only ever one plugin instance for a given name:

    >>> guild.plugin.for_name("gpu") is guild.plugin.for_name("gpu")
    True
