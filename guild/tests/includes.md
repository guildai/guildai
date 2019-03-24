# Guildfile includes

These tests focus on guildfile includes.

Guildfiles support includes by way of a top-level 'include' item.

We'll use [samples/projects/includes](samples/projects/includes) to
illustrate. This project contains `a.yml` and `b.yml` which both
include `common.yml`.

Let's look at `a.yml`.

    >>> gf = guildfile.from_file(sample("projects/includes/a.yml"))

As model 'a' extends 'base' it inherits its flags:

    >>> gf.models["a"].operations
    [<guild.guildfile.OpDef 'a:op1'>, <guild.guildfile.OpDef 'a:op2'>]

We can peek into the data used by `gf` to see how includes work:

    >>> pprint(gf.data)
    [{'config': 'base', 'operations': {'op1': {'exec': 'op1'},
                                       'op2': {'exec': 'op2'}}},
     {'extends': ['base'], 'model': 'a'}]

Note that the 'include' item was replaced with the contents of the
included file.

The remaining tests illustrate various features/behaviors of the
include facility.

## Include lists

Includes can be expressed as a string or as a list of strings. When
expressed as a list, each item is treated as an include.

This is illustrated by
[samples/projects/includes/include-list.yml](samples/projects/includes/include-list.yml):

    >>> gf = guildfile.from_file(sample("projects/includes/include-list.yml"))
    >>> sorted(gf.models)
    ['c', 'uncommon']

    >>> gf.models["c"].operations
    [<guild.guildfile.OpDef 'c:op1'>,
     <guild.guildfile.OpDef 'c:op2'>,
     <guild.guildfile.OpDef 'c:op3'>]

## Include chains

Includes can be
chained. [samples/projects/includes/chain.yml](samples/projects/includes/chain.yml)
illustrates this.

    >>> gf = guildfile.from_file(sample("projects/includes/chain.yml"))
    >>> sorted(gf.models)
    ['a', 'b', 'c']

## Cycles

Cycles are treated as an
error. [samples/projects/includes/cycle.yml](samples/projects/includes/cycle.yml)
introduces a cycle.

    >>> guildfile.from_file(sample("projects/includes/cycle.yml"))
    Traceback (most recent call last):
    GuildfileCycleError: error in cycle in 'includes':
    .../samples/projects/includes/cycle.yml
    (.../samples/projects/includes/cycle.yml ->
     .../samples/projects/includes/cycle-2.yml ->
     .../samples/projects/includes/cycle.yml)

Similarly:

    >>> guildfile.from_file(sample("projects/includes/cycle-2.yml"))
    Traceback (most recent call last):
    GuildfileCycleError: error in cycle in 'includes':
    .../samples/projects/includes/cycle-2.yml
    (.../samples/projects/includes/cycle-2.yml ->
     .../samples/projects/includes/cycle.yml ->
     .../samples/projects/includes/cycle-2.yml)

As well as:

    >>> guildfile.from_file(sample("projects/includes/include-self.yml"))
    Traceback (most recent call last):
    GuildfileCycleError: error in cycle in 'includes':
    .../samples/projects/includes/include-self.yml
    (.../samples/projects/includes/include-self.yml ->
     .../samples/projects/includes/include-self.yml)

## Include from packages

An include may contain a package spec. The package must be in the
system path and contain a `guild.yml` file.

We'll use the sample `projects/includes/include-pkg.yml` to
illustrate. `include-pkg.yml` includes `mnist`, which is a package
spec.

Initially we can't load the Guildfile because `mnist` is not on the
system path:

    >>> guildfile.from_file(sample("projects/includes/include-pkg.yml"))
    Traceback (most recent call last):
    GuildfileIncludeError: error in .../samples/projects/includes/include-pkg.yml:
    cannot find include 'mnist-pkg' (includes must be local to including Guild
    file or a Guild package on the system path)

Let's load `include-pkg.yml` with a modified system path, so we can
find the `mnist` package:

    >>> with SysPath(prepend=[sample("projects"),
    ...                       sample("projects/mnist-pkg")]):
    ...    gf = guildfile.from_file(sample("projects/includes/include-pkg.yml"))

And the models:

    >>> pprint(gf.models)
    {'b': <guild.guildfile.ModelDef 'b'>,
     'expert': <guild.guildfile.ModelDef 'expert'>,
     'intro': <guild.guildfile.ModelDef 'intro'>}

## Bad includes

    >>> guildfile.from_file(sample("projects/includes/bad-include.yml"))
    Traceback (most recent call last):
    GuildfileIncludeError: error in .../projects/includes/bad-include.yml:
    cannot find include 'bad.yml' (includes must be local to including Guild
    file or a Guild package on the system path)
