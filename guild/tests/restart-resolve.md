# Restarts and resource resolution

Guild supports re-resolving of resources.

We use the `restart-resolve` sample project to show Guild's behavior.

    >>> use_project("restart-resolve")

The project defines upstream and downstream operations to demonstrate
resource resolution.

    >>> run("guild ops")
    down          Downstream op - does not re-resolve upstream dependency
    down-resolve  Downstream op - re-resolves upstream dependency
    up            Upstream op - generates a file

Generate two upstream runs.

    >>> run("guild run up --run-id up-1 -y")
    <exit 0>

    >>> run("guild run up --run-id up-2 -y")
    <exit 0>

    >>> run("guild runs")
    [1:up-2]  up  ...  completed
    [2:up-1]  up  ...  completed

The downstream run resolves its upstream dependency using the latest
non-error `up` run.

    >>> run("guild run down --run-id down", timeout=2)
    You are about to run down
      operation:up: up-2
    Continue? (Y/n)
    <exit ...>

    >>> run("guild run down --run-id down -y")
    Resolving operation:up
    Using run up-2 for operation:up

    >>> run("guild select --attr deps")
    operation:up:
      operation:up:
        config: up-2
        paths:
        - ../up-2/file-up-2
        uri: operation:up

    >>> run("guild ls -n")
    file-up-2

We can restart the downstream run using a different upstream run.

    >>> run("guild run --restart down up=up-1", timeout=2)
    You are about to start down (down)
      operation:up: up-1
    Continue? (Y/n)
    <exit ...>

    >>> run("guild run --restart down up=up-1 -y")
    Resolving operation:up
    Skipping resolution of operation:up because it's already resolved

By default, Guild will not re-resolve dependencies. The `deps` attr
and resolved files for the downstream run remain the same.

    >>> run("guild select --attr deps")
    operation:up:
      operation:up:
        config: up-2
        paths:
        - ../up-2/file-up-2
        uri: operation:up

    >>> run("guild ls -n")
    file-up-2

`down-resolve` is configured to re-resolve its upstream dependency.

Generate a `down-resolve` run.

    >>> run("guild run down-resolve --run-id down-resolve -y")
    Resolving operation:up
    Using run up-2 for operation:up

    >>> run("guild select --attr deps")
    operation:up:
      operation:up:
        config: up-2
        paths:
        - ../up-2/file-up-2
        uri: operation:up

    >>> run("guild ls -n")
    file-up-2

Restart the run using a different upstream run.

    >>> run("guild run --restart down-resolve up=up-1", timeout=2)
    You are about to start down-resolve (down-resolve)
      operation:up: up-1
    Continue? (Y/n)
    <exit ...>

    >>> run("guild run --restart down-resolve up=up-1 -y")
    Resolving operation:up
    Using run up-1 for operation:up

Guild re-resolves the upstream dependency. This is reflected in both
the recorded dependencies and the resolved files.

    >>> run("guild select --attr deps")
    operation:up:
      operation:up:
        config: up-1
        paths:
        - ../up-1/file-up-1
        uri: operation:up

    >>> run("guild ls -n")
    file-up-1
    file-up-2

Note that the previously resolved files are still available in the
downstream run directory.
