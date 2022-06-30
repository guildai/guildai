---
doctest: -PY2 -PY3  # Disable tests until we have proper support for Azure.
---

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

    >>> run("guild runs rm -py -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    ...
    <exit 0>

Confirm that Azure source is empty:

    >>> run("guild runs -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    <exit 0>

When we check for deleted runs, we get an error because the Azure blog
storage remote doesn't currently support deleted runs.

    >>> run("guild runs -d -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support '--delete' option
    <exit 1>

Push runs to Azure uat:

    >>> run("guild push guild-uat-azure-blob -y")
    Copying ... to guild-uat-azure-blob
    ...
    <exit 0>

List remote runs:

    >>> run("guild runs -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Show remote run info.

    >>> run("guild runs info -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
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

Prompt to delete remote runs. Non-permanent delete is not supported.

    >>> run("guild runs rm -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support non permanent deletes
    Use the '--permanent' with this command and try again.
    <exit 1>

We need to use the permanent option.

    >>> run("guild runs rm -p -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    WARNING: You are about to permanently delete the following runs on guild-uat-azure-blob:
      [...]  hello  ...  completed  run-2
      [...]  hello  ...  completed  run-1
    Permanently delete these runs? (y/N)
    <exit -9>

Delete remote runs (currently non-permanent deletes are not
supported):

    >>> run("guild runs rm -y -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support non permanent deletes
    Use the '--permanent' with this command and try again.
    <exit 1>

    >>> run("guild runs -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Restore deleted remote runs (doesn't work as non-permanent deletes
aren't supported):

    >>> run("guild runs restore -y -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support this operation
    <exit 1>

Show remote runs:

    >>> run("guild runs -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Delete local runs:

    >>> run("guild runs rm -py")
    Permanently deleted 2 run(s)
    <exit 0>

    >>> run("guild runs")
    <BLANKLINE>
    <exit 0>

Pull remote runs prompt:

    >>> run("guild pull guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    You are about to copy (pull) the following runs from guild-uat-azure-blob:
      [...]  hello  ...  completed  run-2
      [...]  hello  ...  completed  run-1
    Continue? (Y/n)
    <exit -9>

Pull remote runs:

    >>> run("guild pull -y guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
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
    Refreshing run info for guild-uat-azure-blob
    ...
    <exit 0>

    >> run("guild runs purge -y -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    ...
    <exit 0>

    >> run("guild runs -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    <exit 0>

    >> run("guild runs -d -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    <exit 0>

Not supported commands (temp until non-permanent deletes are
supported):

    >>> run("guild runs purge -y -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support this operation
    <exit 1>

    >>> run("guild runs restore -y -r guild-uat-azure-blob")
    guild: remote 'guild-uat-azure-blob' does not support this operation
    <exit 1>

Permanently delete remote runs:

    >>> run("guild runs rm -p -y -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    ...
    Job ... has started
    ...
    Final Job Status: Completed
    <BLANKLINE>
    Refreshing run info for guild-uat-azure-blob
    <exit 0>

    >>> run("guild runs -r guild-uat-azure-blob")
    Refreshing run info for guild-uat-azure-blob
    <exit 0>
