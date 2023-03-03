# Example - Erlang Plugin

This example illustrates how an external application can implement a
Guild AI plugin.

Key points:

- Define an [entry
  point](https://packaging.python.org/en/latest/specifications/entry-points/)
  for `guild.plugins`. See [`setup.py`](setup.py) for details.

- The entry point should specify a class that extends
  `guild.plugin.Plugin`. See
  [`erlang_guild/plugins/escript.py`](erlang_guild/plugins/escript.py).

- Install the package providing the entry point. For "editable"
  installs, use `pip install -e .` from the project directory
  (contains `setup.py`).

- Run `guild check` and verify that the plugin shows up in the list of
  installed plugins.

- To uninstall the plugin, uninstall the applicable package.

Refer to the [`guild.plugin.Plugin`](../../guild/plugin.py) class for the
Plugin API. Each method defined for the `Plugin` class can be
overridden by a plugin to provide plugin-specific functionality.

The Erlang plugin example is a very simple language plugin that knows
how to run Erlang modules as scripts. It supports a novel
configuration scheme for defining flags and using them in arguments to
the script.

Configuration is defined using special comments starting with `%%| `
(two percent signs + pipe + a single space). Multiple contiguous
config lines form a configuration block, which must contain valid
YAML.

For example:

``` erlang
-module(foo).

-export([main/1]).

%% The following comment block is parsed as YAML-defined config by the
%% plugin:

%%| flags:
%%|   bar: 123
%%| args: ${bar}

main([Bar]) -> io:format("bar is ~s\n").
```

The plugin supports two configuration: `flags` and `args`. `flags`
corresponds to the `flags` operation attribute. `args` is
plugin-specific configuration that provides a string containing
references to flag values. The string is formatted as needed to pass
flag values to the script.

In support of running Erlang modules (files ending with `.erl`), the
plugin handles op specs (i.e. the value used in `guild run`) matching
that file format. It returns a model proxy and operation name that can
be used to run the script.

This is but one application of a Guild AI plugin . Refer to
[`guild.plugins`](../../guild/plugins/) for a complete list of built-in
plugins and examples of how plugins are used to extend Guild.

Note that the Guild AI plugin API is not an officially supported API
and is subject to change without notice. However, it is stable and is
not likely to change in a backward-incompatible way.

If you need to extend Guild and can't find a precedent in the built-in
plugins, please feel free to [post a question](https://my.guild.ai) or
[open an issue](https://github.com/guildai/guildai/issues) on GitHub
to get help/advice.

Refer to [TEST.md](TEST.md) for sample usage. To run the tests, use
`guild check -t TEST.md` from this directory.
