# Remote delete runs

This test is used to ensure that all remote runs are deleted.

    >>> quiet("guild runs rm -r guild-uat-ssh -y")

    >>> run("guild runs -r guild-uat-ssh")
    <BLANKLINE>
    <exit 0>
