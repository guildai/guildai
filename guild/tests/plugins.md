# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

## Enumerating plugins

Plugins can be registered by installing packages that provide entry
points for the "guild.plugins" group. For these tests, we want to
ensure we are only working with built-ins:

    >>> guild.plugin.limit_to_builtin()

Use `iter_plugins` to iterate through the list of available plugins:

    >>> sorted([name for name, _ in guild.plugin.iter_plugins()])
    ['config_flags',
     'cpu',
     'dask',
     'disk',
     'dvc',
     'exec_script',
     'gpu',
     'ipynb',
     'memory',
     'perf',
     'python_frameworks',
     'python_script',
     'quarto_document',
     'queue',
     'r_script',
     'resource_flags',
     'skopt']

## Plugin instances

You can get the plugin instance using `for_name`:

    >>> guild.plugin.for_name("gpu")
    <guild.plugins.gpu.GPUPlugin object ...>

There is only ever one plugin instance for a given name:

    >>> guild.plugin.for_name("gpu") is guild.plugin.for_name("gpu")
    True

## Plugins and operations

Guild applies plugins by default based on the operation and
environment. Each plugin is consulted by calling its `enabled_for_op`
method. If it returns true, the plugin is enabled for the operation by
default.

Operations themselves may specify plugins explicitly, which overrides
the default behavior. If an operation specifies a list of plugins,
including an empty list, Guild does not consult any plugins via
`enabled_for_op` and instead selects the plugin if its name or one of
its `provides` names appears in the list of explicitly configured
plugins for the operation.

The sample project `plugins` defines various operations that
illustrate this behavior.

    >>> use_project("plugins")

    >>> run("guild ops")
    defaults
    disabled-boolean
    disabled-list
    explicit-list
    explicit-str
    m:defaults
    m:override

`defaults` uses the default plugins for a Python based operation. We
can examine the list of plugins selected for the operation by either
including the `--debug` option to the run command or by examining the
`plugins` run attribute. We use the later method here.

    >>> run("guild run defaults -y")
    <exit 0>

    >>> run("guild select --attr plugins", ignore="- gpu")
    - cpu
    - disk
    - memory
    - perf
    - python_script

The remaining operations each specify the plugins that apply to the
operation.

`disabled-boolean` uses a boolean to false to disable all plugins.

    >>> run("guild run disabled-boolean -y")
    <exit 0>

    >>> run("guild select --attr plugins")
    []

`disabled-list` uses an empty list to disable all plugins.

    >>> run("guild run disabled-list -y")
    <exit 0>

    >>> run("guild select --attr plugins")
    []

`explicit-str` illustrates that a single plugin may be specified as a
string value.

    >>> run("guild run explicit-str -y")
    <exit 0>

    >>> run("guild select --attr plugins")
    - python_script


`explicit-list` uses a list.

    >>> run("guild run explicit-list -y")
    <exit 0>

    >>> run("guild select --attr plugins")
    - python_frameworks
    - python_script

### Model defaults

If an operation model specifies plugins, that value is used as the
default for each of the model operations. Model operation may override
the plugins value as needed.

The model `m` disables plugins by default.

`m:defaults` does not define plugins and so uses the model configuration.

    >>> run("guild run m:defaults -y")
    <exit 0>

    >>> run("guild select --attr plugins")
    []

`m:override` overrides the model defaults with its own value.

    >>> run("guild run m:override -y")
    <exit 0>

    >>> run("guild select --attr plugins")
    - python_script
