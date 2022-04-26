# Remote Gist

For these tests we use a remote `guild-uat-gist`, which must be
defined and available as a prerequisite to running the tests.

## Init remote

Delete the remote gist if it exists. We can't assert the full output
because we don't know the status at this point.

    >>> quiet("guild remote stop guild-uat-gist -y || true")

Check status again to confirm the gist doesn't exit.

    >>> run("guild remote status guild-uat-gist")
    Getting guild-uat-gist status
    guild: cannot find gist remote 'guild-uat' (denoted by the file
    '[Guild AI] guild-uat.md') for user gar1t
    If the gist is private, you must specify a valid access token
    with GIST_ACCESS_TOKEN.
    For more information see https://my.guild.ai/docs/gists.
    <exit 1>

Create the gist.

    >>> run("guild remote start guild-uat-gist -y")
    Getting guild-uat-gist status
    Creating gist
    Created guild-uat-gist (gist ...) for user gar1t
    Refreshing run info for guild-uat-gist
    <exit 0>

    >>> run("guild remote status guild-uat-gist")
    Getting guild-uat-gist status
    guild-uat-gist (gist ...) is available
    <exit 0>

## List remote runs

List remote runs.

    >>> run("guild runs -r guild-uat-gist", ignore="Permanently added")
    Refreshing run info for guild-uat-gist
    <exit 0>

Try to list deleted remote runs - the gist remote type doesn't support
this.

    >>> run("guild runs -d -r guild-uat-gist")
    guild: remote 'guild-uat-gist' does not support '--deleted' option
    <exit 1>

## Generate local runs in push

Delete local runs in prep for tests.

    >>> quiet("guild runs rm -y")

Generate some sample runs.

    >>> cd(example("hello"))

    >>> run("guild run hello msg='Hello gist' -y")
    Hello gist
    <exit 0>

    >>> run("guild run hello-file -y")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

    >>> cd(example("get-started"))

    >>> run("guild run train.py -y")
    x: 0.100000
    noise: 0.100000
    loss: ...
    <exit 0>

List local runs.

    >>> run("guild runs")
    [1:...]  train.py               ...  completed  noise=0.1 x=0.1
    [2:...]  hello-file (../hello)  ...  completed  file=hello.txt
    [3:...]  hello (../hello)       ...  completed  msg='Hello gist'
    <exit 0>

## Push to remote

Push runs to remote gist.

    >>> run("guild push guild-uat-gist -y", ignore="Permanently added")
    Refreshing run info for guild-uat-gist
    Compressing ...
    Compressing ...
    Compressing ...
    Copying runs to guild-uat-gist
    <exit 0>

List remote runs:

    >>> run("guild runs -r guild-uat-gist")
    Refreshing run info for guild-uat-gist
    [1:...]  train.py               ...  completed  noise=0.1 x=0.1
    [2:...]  hello-file (../hello)  ...  completed  file=hello.txt
    [3:...]  hello (../hello)       ...  completed  msg='Hello gist'
    <exit 0>

## Remote runs info

Show remote run info.

    >>> run("guild runs info -r guild-uat-gist")
    Refreshing run info for guild-uat-gist
    id: ...
    operation: train.py
    from: .../examples/get-started
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: noise=0.1 x=0.1
    sourcecode_digest: ...
    vcs_commit:...
    run_dir: ...
    command: ... -um guild.op_main train --noise 0.1 --x 0.1
    exit_status: 0
    pid:
    tags:
    flags:
      noise: 0.1
      x: 0.1
    scalars:
    <exit 0>

    >>> run("guild runs info 2 -r guild-uat-gist")
    Refreshing run info for guild-uat-gist
    id: ...
    operation: hello-file
    from: .../examples/hello/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: file=hello.txt
    sourcecode_digest: ...
    vcs_commit:...
    run_dir: ...
    command: ... -um guild.op_main cat -- --file hello.txt
    exit_status: 0
    pid:
    tags:
    flags:
      file: hello.txt
    scalars:
    <exit 0>

## Pull remote runs

To illustrate pull, we delete two local runs.

    >>> run("guild runs rm 1 2 -y")
    Deleted 2 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello (../hello)  ...  completed  msg='Hello gist'
    <exit 0>

Prompt to pull all remote runs.

    >>> run("guild pull guild-uat-gist", timeout=15)
    Refreshing run info for guild-uat-gist
    You are about to copy (pull) the following runs from guild-uat-gist:
      [...]  train.py               ...  completed  noise=0.1 x=0.1
      [...]  hello-file (../hello)  ...  completed  file=hello.txt
      [...]  hello (../hello)       ...  completed  msg='Hello gist'
    Continue? (Y/n)
    <exit -9>

Pull all remote runs.

    >>> run("guild pull -y guild-uat-gist")
    Refreshing run info for guild-uat-gist
    Copying ... from guild-uat-gist
    Copying ... from guild-uat-gist
    Copying ... from guild-uat-gist
    <exit 0>

    >>> run("guild runs")
    [1:...]  train.py               ...  completed  noise=0.1 x=0.1
    [2:...]  hello-file (../hello)  ...  completed  file=hello.txt
    [3:...]  hello (../hello)       ...  completed  msg='Hello gist'
    <exit 0>

## Delete remote runs

Prompt to delete remote runs. Non-permanent delete is not supported.

    >>> run("guild runs rm -r guild-uat-gist", timeout=10)
    guild: remote 'guild-uat-gist' does not support non permanent deletes
    Use the '--permanent' with this command and try again.
    <exit 1>

We need to use the permanent option.

    >>> run("guild runs rm -p -r guild-uat-gist", timeout=10)
    Refreshing run info for guild-uat-gist
    WARNING: You are about to permanently delete the following runs on guild-uat-gist:
      [...]  train.py               ...  completed  noise=0.1 x=0.1
      [...]  hello-file (../hello)  ...  completed  file=hello.txt
      [...]  hello (../hello)       ...  completed  msg='Hello gist'
    Permanently delete these runs? (y/N)
    <exit -9>

Try to non-permanently delete runs (not supported).

    >>> run("guild runs rm -y -r guild-uat-gist")
    guild: remote 'guild-uat-gist' does not support non permanent deletes
    Use the '--permanent' with this command and try again.
    <exit 1>

Verify that the remote runs exist.

    >>> run("guild runs -r guild-uat-gist")
    Refreshing run info for guild-uat-gist
    [1:...]  train.py               ...  completed  noise=0.1 x=0.1
    [2:...]  hello-file (../hello)  ...  completed  file=hello.txt
    [3:...]  hello (../hello)       ...  completed  msg='Hello gist'
    <exit 0>

Permanently delete the remote hello runs.

    >>> run("guild runs rm -Fo hello* -p -y -r guild-uat-gist", ignore="Permanently added")
    Refreshing run info for guild-uat-gist
    Deleting ...
    Deleting ...
    Updating runs on guild-uat-gist
    Refreshing run info for guild-uat-gist
    <exit 0>

    >>> run("guild runs -r guild-uat-gist")
    Refreshing run info for guild-uat-gist
    [1:...]  train.py  ...  completed  noise=0.1 x=0.1
    <exit 0>

## Delete the gist

    >>> run("guild remote stop guild-uat-gist -y")
    Getting guild-uat-gist status
    Deleting gist ...
    Clearning local cache
    <exit 0>

    >>> run("guild remote status guild-uat-gist")
    Getting guild-uat-gist status
    guild: cannot find gist remote 'guild-uat' (denoted by the file
    '[Guild AI] guild-uat.md') for user gar1t
    If the gist is private, you must specify a valid access token
    with GIST_ACCESS_TOKEN.
    For more information see https://my.guild.ai/docs/gists.
    <exit 1>

## Not supported commands

Purge:

    >>> run("guild runs purge -y -r guild-uat-gist")
    guild: remote 'guild-uat-gist' does not support this operation
    <exit 1>

Restore:

    >>> run("guild runs restore -y -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support this operation
    <exit 1>
