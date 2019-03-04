# Stop last remote hello op

The `watch` command watches running operation. This test simply shows
the error message that Guild displays when there is no running
operation.

First, list any running ops:

    >>> run("guild runs --running --remote guild-uat-ssh")
    <BLANKLINE>
    <exit 0>

And then try to watch an operation:

    >>> run("guild stop --remote guild-uat-ssh")
    Nothing to stop.
    <exit 0>
