# Example: flags

    >>> cd(example("flags"))

    >>> run("guild ops")
    args-2              Use some CLI options and define defaults
    args-click-default  Use Click API to define CLI
    args-default        Use all CLI options
    config              Use config file to define globals
    config-legacy       Use config file to define globals (legacy method)
    disabled            Disable flag imports
    global              Use a global dict for flag values
    globals-2           Use some global variables and redefine defaults
    globals-default     Use all global variables
    namespace           Use a SimpleNamespace for flag values
    <exit 0>

## Args

    >>> run("guild run args-2 --help-op")
    ???
    Flags:
      b  (default is no)
      f  (default is 1.1)
      s  (default is hola)
    <exit 0>

    >>> run("guild run args-click-default --help-op")
    ???
    Flags:
      b      sample flag (default is no)
      color  sample choices (default is red)
    <BLANKLINE>
             Choices:  red, blue, green
    <BLANKLINE>
      f      sample float (default is 1.1)
      i      sample int (default is 1)
      s      sample string (default is hello)
    <exit 0>

    >>> run("guild run args-default --help-op")
    ???
    Flags:
      b  (default is no)
      f  (default is 1.1)
      i  (default is 1)
      s  (default is hello)
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

## Disabled

    >>> run("guild run disabled --help-op")
    Usage: guild run [OPTIONS] disabled [FLAG]...
    <BLANKLINE>
    Disable flag imports
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <exit 0>

## Globals

Global dict param:

    >>> run("guild run global --help-op")
    ???
    Flags:
      b  (default is yes)
      f  (default is 1.123)
      i  (default is 123)
      l  (default is 1 2 foo)
      s  (default is hello)
    <exit 0>

Sample run:

    >>> run("guild run global b=no i=456 l='2 3 bar baz' -y")
    {'b': False, 'f': 1.123, 'i': 456, 'l': [2, 3, 'bar', 'baz'], 's': 'hello'}
    <exit 0>

Namespace param:

    >>> run("guild run namespace --help-op")
    ???
    Flags:
      b  (default is no)
      f  (default is 1.123)
      i  (default is 123)
      l  (default is 1 2 foo)
      s  (default is hello)
    <exit 0>

Sample run:

    >>> run("guild run namespace b=yes l='2 3 baz bar' i=789 -y")
    namespace(b=True, f=1.123, i=789, l=[2, 3, 'baz', 'bar'], s='hello')
    <exit 0>

Globals support:

    >>> run("guild run globals-2 --help-op")
    ???
    Flags:
      f  (default is 2.2)
      i  (default is 2)
    <exit 0>

    >>> run("guild run globals-default --help-op")
    ???
    Flags:
      b  (default is no)
      f  (default is 1.1)
      i  (default is 1)
      l  (default is 1 2 foo)
      s  (default is hello)
    <exit 0>
