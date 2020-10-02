# pip freeze

By default, Guild does not generate a `pip_freeze` run attribute.

Sample project with two ops - one for the default behavior and another
that disables pip freeze.

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "guild.yml"), """
    ... default: guild.pass
    ... pip-freeze:
    ...   main: guild.pass
    ...   pip-freeze: yes
    ... """)

Verify the ops:

    >>> cd(project_dir)

    >>> run("guild ops")
    default
    pip-freeze
    <exit 0>

Run the default:

    >>> run("guild run default -y")
    <BLANKLINE>
    <exit 0>

    >>> run("guild cat -p .guild/attrs/pip_freeze")
    guild: .../.guild/attrs/pip_freeze does not exist
    <exit 1>

And the op with disabled pip freeze:

    >>> run("guild run pip-freeze -y")
    <BLANKLINE>
    <exit 0>

    >>> run("guild cat -p .guild/attrs/pip_freeze")
    - ...
    <exit 0>
