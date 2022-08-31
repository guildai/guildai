# Notes on Flags Interface

This document contains notes related to Guild's *flags interface*.

**The examples below are not necessarily supported. They are
experimental at the moment.**

## Config Files

Example of using a locally defined `config.yml` file to define flags:

``` yaml
op:
  flags-dest:
    config: config.yml
```

This would be the equivalent of using the `config` resource type:

``` yaml
op:
  requires:
    - config: config.yml
```

The advantage is that `config` flags dest is used to import flag
values defined in `config.yml`. It's also a far more intuitive way to
express the intended behavior.

I think this would mean that `config` style source resolution is
deprecated (with permanent backward compatibility).

## Flags Dest as Mapping

To support flags dest configuration, `flags-dest` becomes a mapping
rather than a string. This implies that `flags-dest: args` is coerced
to `flags-dest: {args: {}}`. With the addition of multiple
destinations (see below) this implies `flags-dest: [args: {}]`.

## Multiple Destinations

Guild could support multiple flags destinations/interfaces:

``` yaml
op:
  flags-import: all
  flags-dest:
    - args: [a, b]
    - globals: [c, d]
    - global:params: [e, f]
    - global: params2
      flags: [e,f]
```

This is a robust scope expansion and we should wait until there's
pressure to implement this. One could argue that it's too much for
Guild to tackle - that anything that complex should be handled by a
user managed wrapper. To support this level of complexity is to
arguably support a clear anti-pattern.

## Python Modules

Per some discussions on Slack, there's a desire to define flags in
module different from main. Something like this:

``` python
# config.py

a = 1
b = 2
```

``` python
# main.py

import config

print(config.a, config.b)
```

``` yaml
# guild.yml

op:
  main: main
  flags-dest:
    globals: config
```

Note that per the "multiple flags dest" topic above, this would coerce
to:

``` yaml
op:
  main: main
  flags-dest:
    - globals:
        module: config
        flags: all
```

In the strange event that `main` requires flags:

``` yaml
op:
  main: main
  flags-dest:
    - globals:
        module: config
        flags: [a,b]
    - globals:
        module: main
        flags: [c]
```

This is pushing reasonable practice, but it's what multiple flags dest
enables.
