# Azure Blob Storage remote

We use `guild-uat-azure-blob` remote for these tests.

    >>> run("guild remote status guild-uat-azure-blob")
    guild-uat-azure-blob (...) is available
    <exit 0>

Generate sample runs for Azure tests.

    >>> cd(example("hello"))

    >>> quiet("guild runs rm -y")

    >>> run("guild run -y hello msg='hello run-1' --label run-1")
    hello run-1
    <exit 0>

    >>> run("guild run -y hello msg='hello run-2' --label run-2")
    hello run-2
    <exit 0>

Assert locally available runs:

    >>> run("guild runs")
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Ensure that all runs are cleared on Azure:

    >>> quiet("guild runs rm -py -r guild-uat-azure-blob")
    >>> quiet("guild runs purge -y -r guild-uat-azure-blob")

Confirm that Azure source is empty:

    >>> run("guild runs -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

    >>> run("guild runs -d -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

Push runs to Azure uat:

    >>> run("guild push guild-uat-azure-blob -y")
    Copying ... to guild-uat-azure-blob
    ...
    <exit 0>

List remote runs:

    >>> run("guild runs -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Show remote run info.

    >>> run("guild runs info -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    id: ...
    operation: hello
    from: .../examples/hello/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: run-2
    sourcecode_digest: ...
    vcs_commit:...
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    tags:
    flags:
      msg: hello run-2
    scalars:
    <exit 0>

Prompt to delete remote runs:

    >>> run("guild runs rm -r guild-uat-azure-blob", timeout=10)
    ???Synchronizing runs with guild-uat-azure-blob...
    You are about to delete the following runs on guild-uat-azure-blob:
      [...]  hello  ...  completed  run-2
      [...]  hello  ...  completed  run-1
    Delete these runs? (Y/n)
    <exit -9>

Delete remote runs (currently non-permanent deletes are not
supported):

    >>> run("guild runs rm -y -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    guild: non permanent delete is not supported by this remote
    Use the '--permanent' with this command and try again.
    <exit 1>

TODO: This is the output that we expect from the pervious command:

    [2mSynchronizing runs with guild-uat-azure-blob[0m
    ...
    <exit 0>

    >>> run("guild runs -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

TODO: When non-permanent delete is reinstated, this should be the
output from the previous command:

    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

List deleted remote runs (currently will alays be empty as
non-permanent deletes aren't supported):

    >>> run("guild runs -d -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

TODO: This should be the output from the previous command:

    [2mSynchronizing runs with guild-uat-azure-blob[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Restore deleted remote runs (doesn't work as non-permanent deletes
aren't supported):

    >>> run("guild runs restore -y -r guild-uat-azure-blob")
    guild: this remote does not support restore at this time
    <exit 1>

TODO: This should be the output from the previous command:

    [2mSynchronizing runs with guild-uat-azure-blob[0m
    ...
    <exit 0>

Show remote runs:

    >>> run("guild runs -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Confirm we don't have any deleted runs:

    >>> run("guild runs -d -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

Delete local runs:

    >>> run("guild runs rm -py")
    Permanently deleted 2 run(s)
    <exit 0>

    >>> run("guild runs")
    <BLANKLINE>
    <exit 0>

Pull remote runs prompt:

    >>> run("guild pull guild-uat-azure-blob", timeout=15)
    Getting remote run info
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    You are about to copy (pull) the following runs from guild-uat-azure-blob:
      [...]  hello  ...  completed  run-2
      [...]  hello  ...  completed  run-1
    Continue? (Y/n)
    <exit -9>

Pull remote runs:

    >>> run("guild pull -y guild-uat-azure-blob")
    Getting remote run info
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    Copying ... from guild-uat-azure-blob
    ...
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Delete and purge remote runs (disabled until non-permanent deletes are
working):

    >> run("guild runs rm -y -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    ...
    <exit 0>

    >> run("guild runs purge -y -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    ...
    <exit 0>

    >> run("guild runs -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

    >> run("guild runs -d -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

Permanently delete remote runs:

    >>> run("guild runs rm -p -y -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    ...
    Job ... has started
    ...
    Final Job Status: Completed
    <BLANKLINE>
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>

    >>> run("guild runs -r guild-uat-azure-blob")
    [2mSynchronizing runs with guild-uat-azure-blob[0m
    <exit 0>
