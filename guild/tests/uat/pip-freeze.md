# pip freeze

By default, Guild generates a `pip_freeze` run attribute for Python
based ops.

Generate a sample project with three operations:

 - Standard Python operation
 - Standard Python operation with pip freeze disabled
 - Non-Python operation

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "guild.yml"), """
    ... default: guild.pass
    ... no-pip-freeze:
    ...   main: guild.pass
    ...   pip-freeze: no
    ... non-python:
    ...   exec: echo hello
    ... """)

    >>> use_project(project_dir)

    >>> run("guild ops")
    default
    no-pip-freeze
    non-python

The default operation generates a `pip_freeze` attribute.

    >>> run("NO_PIP_FREEZE= guild run default -y")
    <exit 0>

    >>> run("guild select --attr pip_freeze")
    ???
    click==8...
    ...
    <exit 0>

`no-pip-freeze` does not generate `pip_freeze`.

    >>> run("NO_PIP_FREEZE= guild run no-pip-freeze -y")
    <exit 0>

    >>> run("guild select --attr pip_freeze")
    guild: no such run attribute 'pip_freeze'
    <exit 1>

`non-python` similarly does not generate `pip_freeze`.

    >>> run("NO_PIP_FREEZE= guild run non-python -y")
    hello

    >>> run("guild select --attr pip_freeze")
    guild: no such run attribute 'pip_freeze'
    <exit 1>
