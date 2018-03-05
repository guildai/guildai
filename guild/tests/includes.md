# Guildfile includes

These tests focus on guildfile includes.

Guildfiles support includes by way of a top-level 'include' item.

We'll use [samples/projects/includes](samples/projects/includes) to
illustrate. This project contains `a.yml` and `b.yml` which both
include `common.yml`.

Let's look at `a.yml`.

    >>> from guild import guildfile
    >>> gf = guildfile.from_file(sample("projects/includes/a.yml"))

As model 'a' extends 'base' it inherits its flags:

    >>> gf.models["a"].flags
    [<guild.guildfile.FlagDef 'base-flag-1'>,
     <guild.guildfile.FlagDef 'base-flag-2'>]

We can peek into the data used by `gf_a` to see how includes work:

    >>> pprint(gf.data)
    [{'flags': {'base-flag-1': 'bf1', 'base-flag-2': 'bf2'}, 'model': 'base'},
     {'extends': 'base', 'model': 'a'}]

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
    ['base', 'c', 'uncommon']

    >>> gf.models["c"].flags
    [<guild.guildfile.FlagDef 'base-flag-1'>,
     <guild.guildfile.FlagDef 'base-flag-2'>,
     <guild.guildfile.FlagDef 'uncommon-flag-1'>]

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
