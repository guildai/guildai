# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

## Enumerating plugins

Use `iter_plugins` to iterate through the list of available plugins:

    >>> sorted(guild.plugin.iter_plugins())
    ['gpu', 'keras']

## Plugin instances

You can get the plugin instance using `for_name`:

    >>> guild.plugin.for_name("gpu")
    <guild.plugins.gpu.GPUPlugin object at ...>

There is only ever one plugin instance for a given name:

    >>> guild.plugin.for_name("gpu") is guild.plugin.for_name("gpu")
    True
