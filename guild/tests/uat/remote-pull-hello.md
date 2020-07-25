# Pull from remote server

This test assumes that there are two remote runs, each from the
`hello` example. Only the last two runs are pulled.

We first preview the runs:

    >>> run("guild pull guild-uat 1:2", timeout=5)
    Getting remote run info
    You are about to copy (pull) the following runs from guild-uat:
      [...]  gpkg.hello/hello-op    ...  completed  remote-run-123
      [...]  gpkg.hello/hello-file  ...  completed  file=hello.txt
    Continue? (Y/n)
    <exit -9>

Then pull:

    >>> run("guild pull guild-uat 1:2 -y")
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
    [1:...]  gpkg.hello/hello-op    ...  completed  remote-run-123
    [2:...]  gpkg.hello/hello-file  ...  completed  file=hello.txt
    [3:...]  test.py (...)          ...  completed  x=1
    [4:...]  op-2 (...)             ...  completed
    [5:...]  op-1 (...)             ...  completed
    <exit 0>

Sync the latest run:

    >>> run("guild sync `guild select`")
    <exit 0>
