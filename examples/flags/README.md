# Guild Example: `flags`

This example demonstrates various methods of defining and using flags.

- [guild.yml](guild.yml) - Project Guild file
- [args.py](args.py) - Flags defined as command line options using
  `argparse`
- [args_click.py](args_click.py) - Flags defined as command line
  options using [Click](https://click.palletsprojects.com/)
- [config.py](config.py) - Flags defined in YAML config file
- [config2.py](config2.py) - Flags defined in JSON config file
- [config3.py](config3.py) - Flags defined in INI config file
- [flags.ini](flags.ini) - INI file used with `config-3` operation
- [flags.json](flags.json) - JSON file used with `config-2` operation
- [flags.yml](flags.yml) - YAML file used with `config` operation
- [global_dict.py](global_dict.py) - Flags defined in a global dict
- [global_namespace.py](global_namespace.py) - Flags defined in a
  global `SimpleNamespace` variable
- [globals.py](globals.py) - Flags defined as global variables

To show flag settings for all operations, change to this directory and run:

    $ guild help

Refer to [`guild.yml`](guild.yml) for configuration details.
