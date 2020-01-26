# S3 push/pull

Generate sample runs for S3 tests.

    >>> cd(example("hello"))

    >>> quiet("guild runs rm -y")

    >>> run("guild run -y hello msg='hello run-1' --label run-1")
    hello run-1
    <exit 0>

    >>> run("guild run -y hello msg='hello run-2' --label run-2")
    hello run-2
    <exit 0>

Assert locally available runs:

    >> run("guild runs")
    [1:...]  hello:hello  ...  completed  run-2
    [2:...]  hello:hello  ...  completed  run-1
    <exit 0>

Ensure that all runs are cleared on S3:

    >>> quiet("guild runs rm -py -r guild-uat-s3")
    >>> quiet("guild runs purge -y -r guild-uat-s3")

Confirm that S3 source is empty:

    >>> run("guild runs -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    <exit 0>

    >>> run("guild runs -d -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    <exit 0>

Push runs to S3 uat:

    >>> run("guild push guild-uat-s3 -y")
    Copying ... to guild-uat-s3
    ...
    <exit 0>

List remote runs:

    >>> run("guild runs -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Prompt to delete remote runs:

    >>> run("guild runs rm -r guild-uat-s3", timeout=10)
    ???Synchronizing runs with guild-uat-s3...
    You are about to delete the following runs on guild-uat-s3:
      [...]  hello  ...  completed  run-2
      [...]  hello  ...  completed  run-1
    Delete these runs? (Y/n)
    <exit -9>

Delete remote runs:

    >>> run("guild runs rm -y -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    ...
    <exit 0>

    >>> run("guild runs -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    <exit 0>

List deleted remote runs:

    >>> run("guild runs -d -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Restore deleted remote runs:

    >>> run("guild runs restore -y -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    ...
    <exit 0>

Show remote runs:

    >>> run("guild runs -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Confirm we don't have any deleted runs:

    >>> run("guild runs -d -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    <exit 0>

Delete local runs:

    >>> run("guild runs rm -py")
    Permanently deleted 2 run(s)
    <exit 0>

    >>> run("guild runs")
    <BLANKLINE>
    <exit 0>

Pull remote runs prompt:

    >>> run("guild pull guild-uat-s3", timeout=15)
    Getting remote run info
    [2mSynchronizing runs with guild-uat-s3[0m
    You are about to copy (pull) the following runs from guild-uat-s3:
      [...]  hello  ...  completed  run-2
      [...]  hello  ...  completed  run-1
    Continue? (Y/n)
    <exit -9>

Pull remote runs:

    >>> run("guild pull -y guild-uat-s3")
    Getting remote run info
    [2mSynchronizing runs with guild-uat-s3[0m
    Copying ... from guild-uat-s3
    ...
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Delete and purge remote runs:

    >>> run("guild runs rm -y -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    ...
    <exit 0>

    >>> run("guild runs purge -y -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    ...
    <exit 0>

    >>> run("guild runs -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    <exit 0>

    >>> run("guild runs -d -r guild-uat-s3")
    [2mSynchronizing runs with guild-uat-s3[0m
    <exit 0>
