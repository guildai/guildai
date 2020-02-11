# Guild Example: `dependencies`

This example illustrates each of Guild's supported dependency types.

- [guild.yml](guild.yml) - Project Guild file
- [file.txt](file.txt) - Sample file used in dependency examples
- [dir](dir) - Sample directory used in dependency examples
- [config.yml](config.yml) - Sample configuration file used in dependencies
- [config.json](config.json) - Sample configuration file used in dependencies

See [guild.yml](guild.yml) for a list of examples.

## Operations

```
all                        Run all non-broken depepdency operations
config                     Configuration file dependency
customizable-file          File dependency that can be customized with flag
dir                        Directory dependency
dir-op                     Operation directory dependency
downstream                 Downstream operation with upstream dependency
file                       File dependency
file-op                    Operation file dependency
json-config                Config dependency using JSON config format
missing-file               Broken file dependency
missing-module             Broken module dependency
missing-named-file         Broken file dependency with alternative name
modified-config            Config dependency with modified values
modules                    Module dependency
unsupported-config-format  Broken dependency using unsupported config format
url                        URL dependency
```

## Run Examples

Change to this directory and list available operations:

```
$ guild ops
```

Run any of the operations to see how Guild resolves the dependencies.

Verify resolved files using `guild ls` to list files for the latest
run:

```
guild ls
```

Use `guild cat -p <path>` to show contents of resolve configuration
files, where applicable.

For example, after running `guild run config`, use the following to
view the resolved configuration file:

```
$ guild cat -p config.yml
```

To run all non-broken dependency examples, run:

```
$ guild run all
```
