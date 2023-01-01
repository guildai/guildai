---
# Tests use shell scripts that don't run on non-POSIX systems

doctest: -WINDOWS
---

# Batch runs - Guild file optimizers

Optimizers may be defined in a Guild file, in which case the
configuration from the Guild file is used as default when optimizing.

We'll use the `optimizers` sample project.

    >>> use_project("optimizers")

There are multiple scenarios that we test:

- Define a single optimizer with default flags
- Define multiple optimizers, designating one as a default
- Define multiple optimizers, without a default

## Single optimizer config

The `opt-test-1` operation is configured to use a single optimizer
`tune-echo`. When we specify the `--optimize,-O` option for a run,
Guild uses `tune-echo`.

    >>> run("guild run opt-test-1 --optimize -y")
    Running tune-echo --alpha 0.1 --beta 0.2

This operation is only a stub - it doesn't perform any work.

    >>> run("guild runs -s")
    [1]  opt-test-1+tune-echo  completed  alpha=0.1 beta=0.2

We can change the optimizer flags using `-Fo` options.

    >>> run("guild run opt-test-1 --optimize -Fo beta=0.3 -y")
    Running tune-echo --alpha 0.1 --beta 0.3

While `tune-echo` is used by default, we can specify an alternative
optimizer using the `--optimizer` option.

    >>> run("guild run opt-test-1 --optimizer tune-echo-2 -y")
    Running tune-echo-2 --beta 0.4 --gamma 3

And similarly, override optimizer flags.

    >>> run("guild run opt-test-1 -o tune-echo-2 -Fo beta=0.5 -Fo gamma=5 -y")
    Running tune-echo-2 --beta 0.5 --gamma 5

`opt-test-2` operation is configured with a single optimizer and
redefines an optimizer flag.

    >>> run("guild run opt-test-2 -O -y")
    Running tune-echo --alpha 0.1 --beta 0.3

We can redefine these flags in the run command.

    >>> run("guild run opt-test-2 -O -Fo alpha=0.2 -Fo beta=0.4 -y")
    Running tune-echo --alpha 0.2 --beta 0.4

## Multiple optimizers with default

The `opt-test-3` operation defines two optimizers, one of which is
default ('o2').

    >>> run("guild run opt-test-3 -Oy")
    Running tune-echo-2 --beta 0.6 --gamma 4

We can specify an optimizer using its configured name.

    >>> run("guild run opt-test-3 -o o1 -y")
    Running tune-echo --alpha 0.1 --beta 0.2

    >>> run("guild run opt-test-3 -o o2 -y")
    Running tune-echo-2 --beta 0.6 --gamma 4

Optimizer flags can be redefined when a name is use.

    >>> run("guild run opt-test-3 -o o1 -Fo alpha=0.9 -y")
    Running tune-echo --alpha 0.9 --beta 0.2

We can also specify the optimizer operation name, in which case the
optimizer default flags are used.

    >>> run("guild run opt-test-3 -o tune-echo-2 -y")
    Running tune-echo-2 --beta 0.4 --gamma 3

## Multiple optimizers without default

The `opt-test-4` operation defines two optimizers, but none are
designated as default.

    >>> run("guild run opt-test-4 -O -y")
    guild: no default optimizer defined for opt-test-4
    Specify one of the following with '--optimizer': alt-tune, tune-echo
    <exit 1>

Specify one of the supported optimizers.

    >>> run("guild run opt-test-4 -o alt-tune -y")
    Running tune-echo-2 --beta 0.4 --gamma 3

Specify an unsupported optimizer.

    >>> run("guild run opt-test-4 -o not-an-optimizer -y")
    guild: operation 'not-an-optimizer' is not defined for this project
    Try 'guild operations' for a list of available operations.
    <exit 1>

Note again that the optimizer value is treated as an op spec when it
doesn't match a named optimizer. We can use any available operation
with the optimizer flag.

    >>> run("guild run opt-test-4 -o tune-echo-2 -y")
    Running tune-echo-2 --beta 0.4 --gamma 3
