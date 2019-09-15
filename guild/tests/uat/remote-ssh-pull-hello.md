# Pull from remote server

This test assumes that there are two remote runs, each from the
`hello` example. Only the last two runs are pulled.

We first preview the runs:

    >>> run("guild pull guild-uat-ssh 1:2", timeout=5)
    Getting remote run info
    You are about to copy (pull) the following runs from guild-uat-ssh:
      [...]  hello/hello:from-file  ...  completed  remote-run-123
      [...]  hello/hello:from-flag  ...  completed  message='Howdy Guild!'
    Continue? (Y/n)
    <exit -9>

Then pull:

    >>> run("guild pull guild-uat-ssh 1:2 -y")
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
    [1:...]   hello/hello:from-file  ...  completed  remote-run-123
    [2:...]   hello/hello:from-flag  ...  completed  message='Howdy Guild!'
    ...
    <exit 0>
