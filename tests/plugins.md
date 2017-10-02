# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

## Enumerating plugins

    >>> for plugin in sorted(guild.plugin.iter_plugins()):
    ...   print(plugin)
    ('keras', 'guild.plugins.keras.KerasPlugin')

## Instantiating plugins

Create a plugin instance using `plugin`, providing the plugin class
name:

    >>> guild.plugin.plugin("guild.plugins.keras.KerasPlugin")
    <guild.plugins.keras.KerasPlugin object at ...>
