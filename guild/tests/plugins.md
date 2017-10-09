# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

We need to explicitly initialize plugins by calling `init_plugins`:

    >>> guild.plugin.init_plugins()

## Enumerating plugins

Use `iter_plugins` to iterate through the list of available plugins:

    >>> sorted(guild.plugin.iter_plugins())
    [('cpu', <guild.plugins.cpu.CPUPlugin object ...>),
     ('disk', <guild.plugins.disk.DiskPlugin object ...>),
     ('gpu', <guild.plugins.gpu.GPUPlugin object ...>),
     ('keras', <guild.plugins.keras.KerasPlugin object ...>),
     ('memory', <guild.plugins.memory.MemoryPlugin object ...>)]

## Plugin instances

You can get the plugin instance using `for_name`:

    >>> guild.plugin.for_name("gpu")
    <guild.plugins.gpu.GPUPlugin object ...>

There is only ever one plugin instance for a given name:

    >>> guild.plugin.for_name("gpu") is guild.plugin.for_name("gpu")
    True
