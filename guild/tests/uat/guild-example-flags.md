# Example: flags

    >>> cd(example("flags"))

    >>> run("guild ops")
    args-2              Use some CLI options and define defaults
    args-click-default  Use Click API to define CLI
    args-default        Use all CLI options
    config              Use config file to define globals
    config-legacy       Use config file to define globals (legacy method)
    disabled            Disable flag imports
    globals-2           Use some global variables and redefine defaults
    globals-default     Use all global variables
    <exit 0>

## Config support

    >>> run("guild run config --help-op")
    ???
    Flags:
      b  (default is no)
      f  (default is 1.123)
      i  (default is 123)
      l  (default is 1 1.2 blue true)
      s  (default is Howdy Guild)
    <exit 0>

    >>> run("guild run config b=yes i=456 l='no green 2' -y")
    Resolving config:flags.yml dependency
    {'b': True, 'f': 1.123, 'i': 456, 'l': [False, 'green', 2], 's': 'Howdy Guild'}
    <exit 0>

Legacy support:

    >>> run("guild run config-legacy --help-op")
    ???
    Flags:
      b  (default is no)
      f  (default is 1.123)
      i  (default is 1)
    <exit 0>

    >>> run("guild run config-legacy i=456 b=yes -y")
    Resolving config:flags.yml dependency
    {'b': True,
     'f': 1.123,
     'i': 456,
     'l': [1, 1.2, 'blue', True],
     's': 'Howdy Guild'}
    <exit 0>
