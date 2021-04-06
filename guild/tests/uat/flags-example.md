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

    >>> run("guild run args-click-default -y")
    Flags: 1 1.1 True hello red
    <exit 0>

    >>> run("guild run args-click-default i=9 f=9.9 s=hola c=green -y")
    Flags: 9 9.9 True hola green
    <exit 0>

    >>> run("guild run args-click-default c=yellow -y")
    Unsupported value for 'c' - supported values are:
    <BLANKLINE>
      red
      blue
      green
    <BLANKLINE>
    Run the command again using one of these options.
    <exit 1>
