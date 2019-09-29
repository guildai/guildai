# Remote delete runs

Ensure all remote runs are deleted:

    >>> quiet("guild runs rm -r guild-uat -y")

    >>> run("guild runs -r guild-uat")
    <BLANKLINE>
    <exit 0>
