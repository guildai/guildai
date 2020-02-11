# Anonymous models

An anonymous model a model that has an empty name ('').

    >>> gf = guildfile.for_string("""
    ... - model: ''
    ... """)

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

Anonymous models are most commonly defined implicitly when a Guild
file is a map of operations:

    >>> gf = guildfile.for_string("""
    ...   op1: {exec: 'true'}
    ...   op2: {exec: 'true'}
    ...   op3: {exec: 'true'}
    ... """)

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'op1'>,
     <guild.guildfile.OpDef 'op2'>,
     <guild.guildfile.OpDef 'op3'>]

An anonymous model can also be defined implicitly by defining
`operations` in a top-level and NOT defining `model` or `config`.

    >>> gf = guildfile.for_string("""
    ... - operations:
    ...     op1: guild.pass
    ...     op2: guild.pass
    ...     op3: guild.pass
    ... """)

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'op1'>,
     <guild.guildfile.OpDef 'op2'>,
     <guild.guildfile.OpDef 'op3'>]

Defining `config` with `operations`:

    >>> gf = guildfile.for_string("""
    ... - operations:
    ...     op1: guild.pass
    ...     op2: guild.pass
    ...     op3: guild.pass
    ...   config: foo
    ... """)

    >>> gf.models
    {}

## Iterating anonymous models

Anonymous models are still visible via `guild.model.iter_models`.

    >>> from guild.model import iter_models

Let's view the models in the `anonymous-model` sample project:

    >>> project = sample("projects", "anonymous-model")

We need to iterate in the context of the configured model path:

    >>> with ModelPath([project]):
    ...     list(iter_models())
    [<guild.model.GuildfileModel ''>]

While anonymous models are visible via normal iteration, they are not
displayed to the user.

Here's the result from `guild.commands.models_impl`, which is
responsible for displaying models to the user:

    >>> from guild.commands import models_impl
    >>> with ModelPath([project]):
    ...     list(models_impl.iter_models())
    []
