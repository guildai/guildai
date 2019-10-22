skip-windows: yes

Uses OS scrcipts that don't run on Windows.

# Batch runs - Guild file optimizers

Optimizers may be defined in a Guild file, in which case the
configuration from the Guild file is used as default when optimizing.

We'll use the `optimizers` sample project.

    >>> project = Project(sample("projects", "optimizers"))

There are multiple scenarios that we test:

- Define a single optimizer with default flags
- Define multiple optimizers, designating one as a default
- Define multiple optimizers, without a default

## Single optimizer config

The `opt-test-1` operation defines a single optimizer
`tune-echo`. When we specify the `optimize` option for a run, Guild
uses the configured optimizer:

    >>> project.run("opt-test-1", optimize=True)
    Resolving file:tune-echo dependency
    tune-echo --alpha 0.1 --beta 0.2

We can override default optimizer flags:

    >>> project.run("opt-test-1", optimize=True, opt_flags={"beta": 0.3})
    Resolving file:tune-echo dependency
    tune-echo --alpha 0.1 --beta 0.3

We can still always specify a different optimizer:

    >>> project.run("opt-test-1", optimizer="tune-echo-2")
    Resolving file:tune-echo dependency
    tune-echo-2 --beta 0.4 --gamma 3

And similarly, override optimizer flags:

    >>> project.run("opt-test-1", optimizer="tune-echo-2",
    ...             opt_flags={"beta": 0.5, "gamma": 5})
    Resolving file:tune-echo dependency
    tune-echo-2 --beta 0.5 --gamma 5

The `opt-test-2` operation also defines a single optimizer, but
redefines an optimizer flag.

    >>> project.run("opt-test-2", optimize=True)
    Resolving file:tune-echo dependency
    tune-echo --alpha 0.1 --beta 0.3

Again, we can redefine these flags in the run command:

    >>> project.run("opt-test-2", optimize=True,
    ...             opt_flags={"alpha": 0.2, "beta": 0.4})
    Resolving file:tune-echo dependency
    tune-echo --alpha 0.2 --beta 0.4

## Multiple optimizers with default

The `opt-test-3` operation defines two optimizers, one of which is
default ('o2').

    >>> project.run("opt-test-3", optimize=True)
    Resolving file:tune-echo dependency
    tune-echo-2 --beta 0.6 --gamma 4

We can specify an alternative optimizer explicitly:

    >>> project.run("opt-test-3", optimizer="o1")
    Resolving file:tune-echo dependency
    tune-echo --alpha 0.1 --beta 0.2

    >>> project.run("opt-test-3", optimizer="o2")
    Resolving file:tune-echo dependency
    tune-echo-2 --beta 0.6 --gamma 4

Note that we use the optimizer name as defined in the Guild file. We
can always specify the optimizer operation directly, in which case the
optimizer default flags are used:

    >>> project.run("opt-test-3", optimizer="tune-echo-2")
    Resolving file:tune-echo dependency
    tune-echo-2 --beta 0.4 --gamma 3

## Multiple optimizers without default

The `opt-test-4` operation defines two optimizers, but none are
designated as default.
