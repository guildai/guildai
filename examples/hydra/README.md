---
doctest-type: bash
---

# Guild AI and Hydra

This examples shows how Guild is used with Hydra based scripts.

## Example 1

The first example, implemented in [`my_app_1.py`](my_app_1.py), uses
command arguments to specify config values. This follows the [simple
command line application
example](https://hydra.cc/docs/tutorials/basic/your_first_app/simple_cli).

In this case, all config is specified via arguments. Flags must be
explicitly defined in [guild.yml](guild.yml) as there are no other
definitions to draw from.

    $ guild run basic-tutorial-1 user=test -y
    db:
      driver: mysql
      user: test
      password: secret
    <exit 0>

## Example 2

The second example, implemented in [`my_app_2.py`](my_app_2.py) uses
[`config.yaml`](config.yaml) to define config, following the [config
file
example](https://hydra.cc/docs/tutorials/basic/your_first_app/config_file).

    $ guild run basic-tutorial-2 db.user=test -y
    Resolving config:config.yaml dependency
    db:
      driver: mysql
      password: secret
      user: test
    <exit 0>

`basic-tutorial-2` uses `config.yaml` as the flags interface. It
copies an updated config file to the run directory source path, which
is where hydra expects it.

    $ guild cat -p .guild/sourcecode/config.yaml
    db:
      driver: mysql
      password: secret
      user: test
    <exit 0>

## Example 3

The third example, implemented in [`my_app_3.py`](my_app_3.py) uses
[Hydra config groups] and argparse to expose a group name and
additional config values via flag values.

    $ guild run basic-tutorial-3
    >   db=postgresql
    >   db-config="db.timeout=60 db.user=bob" -y
    db:
      driver: postgresql
      pass: drowssap
      timeout: 60
      user: bob
    <exit 0>

This last approach relies on an intermediary interface - a standard
argparse CLI - to adapt Guild to Hydra config. Guild does not support
pass-through of arbitrary arguments to a script. Any operation config
must be specified using the flags interface.
