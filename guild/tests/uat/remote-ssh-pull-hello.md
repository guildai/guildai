# Pull from remote server

This test assumes that there are two remote runs, each from the
`hello` example. Only the last two runs are pulled.

    >>> run("guild pull 1:2 guild-uat-ssh -y")
    Getting remote run info
    Copying ...
    receiving incremental file list
    ...
    Copying ...
    receiving incremental file list
    ...
    <exit 0>

The latest runs:

    >>> run("guild runs -a")
    [1:...]   hello/hello:from-flag  ... ...  completed  remote-run-123
    [2:...]   hello/hello:default    ... ...  completed
    ...
    <exit 0>
