# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

## Enumerating plugins

Use `iter_plugins` to iterate through the list of available plugins:

    >>> sorted(guild.plugin.iter_plugins())
    [('gpu', 'guild.plugins.gpu.GPUPlugin'),
     ('keras', 'guild.plugins.keras.KerasPlugin')]

## Instantiating plugins

Plugins can be instantiated using a plugin name or a fully qualified
class name.

Here's a plugin instance for the "gpu" plugin:

    >>> guild.plugin.for_name("gpu")
    <guild.plugins.gpu.GPUPlugin object at ...>

Here's a plugin instance for the class name corresponding to the "gpu"
plugin:

    >>> guild.plugin.for_class("guild.plugins.gpu.GPUPlugin")
    <guild.plugins.gpu.GPUPlugin object at ...>

Each plugin instance is separate:

    >>> guild.plugin.for_name("gpu") != guild.plugin.for_name("gpu")
    True
