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

    $ guild run basic-tutorial-1 user=test password=xxx -y
    db:
      driver: mysql
      user: test
      password: xxx

## Example 2

The second example, implemented in [`my_app_2.py`](my_app_2.py) uses
[`config.yaml`](config.yaml) to define config, following the [config
file
example](https://hydra.cc/docs/tutorials/basic/your_first_app/config_file).

    $ guild run basic-tutorial-2 db.user=test db.driver=postgresql -y
    Resolving config:config.yaml
    db:
      driver: postgresql
      password: secret
      user: test

`basic-tutorial-2` uses `config.yaml` as the flags interface. It
copies an updated config file to the run directory -- the source code
root -- which is where hydra expects it.

    $ guild cat -p config.yaml
    db:
      driver: postgresql
      password: secret
      user: test

## Example 3

The third example, implemented in [`my_app_3.py`](my_app_3.py) uses
[Hydra config
groups](https://hydra.cc/docs/tutorials/basic/your_first_app/config_groups)
and argparse to expose a group name and additional config values via
flag values.

    $ guild run basic-tutorial-3
    >   db=postgresql
    >   db-config="db.timeout=60 db.user=bob db.pass='my secret'" -y
    db:
      driver: postgresql
      pass: my secret
      timeout: 60
      user: bob

This last approach relies on an intermediary interface to adapt Guild
to Hydra config. Guild does not support pass-through of arbitrary
arguments to a script and does not support flag groups/value-dependent
flag defs.
