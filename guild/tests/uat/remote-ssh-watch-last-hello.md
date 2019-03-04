# Watch last remote hello op

The `watch` command watches running operation. This test simply shows
the error message that Guild displays when there is no running
operation.

First, list any running ops:

    >>> run("guild runs --running --remote guild-uat-ssh")
    <BLANKLINE>
    <exit 0>

And then try to watch an operation:

    >>> run("guild watch --remote guild-uat-ssh")
    guild: nothing to watch
    You can view the output of a specific run using 'guild watch RUN'.
    <exit 1>
