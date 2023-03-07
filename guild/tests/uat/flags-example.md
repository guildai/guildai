# Flags example

    >>> cd(example("flags"))

## Args

    >>> run("guild run args-default -y")
    Flags: 1 1.1 False hello
    <exit 0>

    >>> run("guild run args-default i=9 f=9.9 s=hola -y")
    Flags: 9 9.9 False hola
    <exit 0>

## Globals

    >>> run("guild run globals-default -y")
    Flags: 1 1.1 False hello
    <exit 0>

    >>> run("guild run globals-default i=9 f=9.9 s=hola -y")
    Flags: 9 9.9 False hola
    <exit 0>

## Click Args

    >>> run("guild run args_click.py -y")
    Flags: 1 1.1 False hello red
    <exit 0>

    >>> run("guild run args-click-default -y")
    Flags: 1 1.1 False hello red
    <exit 0>

    >>> run("guild run args-click-default i=9 f=9.9 s=hola c=green b=yes -y")
    Flags: 9 9.9 True hola green
    <exit 0>

    >>> run("guild run args_click.py i=9 f=9.9 s=hola c=green b=yes -y")
    Flags: 9 9.9 True hola green
    <exit 0>

    >>> run("guild run args-click-default c=yellow -y")
    Unsupported value for 'c' - supported values are:
    <BLANKLINE>
      red
      blue
      green
      gray
    <BLANKLINE>
    Run the command again using one of these options.
    <exit 1>

## Config

YAML based:

    >>> run("guild run config -y")
    Resolving config:flags.yml
    {'b': False,
     'f': 1.123,
     'i': 123,
     'l': [1, 1.2, 'blue', True],
     's': 'Howdy Guild'}
    <exit 0>

    >>> run("guild run config b=yes i=321 l='2 2.3 green no' -y")
    Resolving config:flags.yml
    {'b': True,
     'f': 1.123,
     'i': 321,
     'l': [2, 2.3, 'green', False],
     's': 'Howdy Guild'}
    <exit 0>

    >>> run("guild cat -p flags.yml")
    b: true
    f: 1.123
    i: 321
    l:
    - 2
    - 2.3
    - green
    - false
    s: Howdy Guild
    <exit 0>

JSON based:

    >>> run("guild run config-2 -y")
    Resolving config:flags.json
    {'b': False,
     'f': 1.123,
     'i': 123,
     'l': [1, 1.2, 'blue', True],
     's': 'Howdy Guild'}
    <exit 0>

    >>> run("guild run config-2 b=yes i=321 l='2 2.3 green no' -y")
    Resolving config:flags.json
    {'b': True,
     'f': 1.123,
     'i': 321,
     'l': [2, 2.3, 'green', False],
     's': 'Howdy Guild'}
    <exit 0>

    >>> run("guild cat -p flags.json")
    {"b": true, "f": 1.123, "i": 321, "l": [2, 2.3, "green", false], "s": "Howdy Guild"}
    <exit 0>

INI based:
    
    >>> run("guild run config-3 --help-op")
    ???
    Flags:
      flags.b  (default is no)
      flags.f  (default is 1.123)
      flags.i  (default is 123)
      flags.l  (default is '1 1.2 blue yes')
      flags.s  (default is 'Howdy Guild')

    >>> run("guild run config-3 -y")
    Resolving config:flags.ini
    [flags]
    b = False
    f = 1.123
    i = 123
    l = [1, 1.2, 'blue', True]
    s = Howdy Guild

    >>> run("guild run config-3 flags.b=yes flags.i=321 flags.l='2 2.3 green no' -y")
    Resolving config:flags.ini
    [flags]
    b = True
    f = 1.123
    i = 321
    l = [2, 2.3, 'green', False]
    s = Howdy Guild

    >>> run("guild cat -p flags.ini")
    [flags]
    b = True
    f = 1.123
    i = 321
    l = [2, 2.3, 'green', False]
    s = Howdy Guild