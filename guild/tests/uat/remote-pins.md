# Pins remote

We first configure the pins remote:

    >>> txt = open("/tmp/pins-test-config.yml", "wt")
    >>> out = txt.write("""
    ... remotes:
    ...     guild-uat-pins:
    ...         type: pins
    ...         board: folder
    ...         config:
    ...             path: /tmp/pins-local-folder
    ...             
    ... """)
    >>> txt.close()

Override `run` so we always use the configuration above

    >>> _run = run
    >>> def run(x):
    ...     _run(f"GUILD_CONFIG='/tmp/pins-test-config.yml' {x}")
    >>> run("rm -rf /tmp/pins-local-folder")
    <exit 0>

Now check status works:

    >>> run("guild remote status guild-uat-pins")
    guild-uat-pins (Pins board ...) is available
    <exit 0>

Make some test runs:

    >>> cd(example("hello"))
    >>> quiet("guild runs rm -y")
    
    >>> run("guild run -y hello msg='hello run-1' --label run-1")
    hello run-1
    <exit 0>
    
    >>> run("guild run -y hello msg='hello run-2' --label run-2")
    hello run-2
    <exit 0>

Push runs to pins remote:

    >>> run("guild runs push guild-uat-pins -y")
    Pushing runs to pins board...
    ...
    Refreshing run info for guild-uat-pins
    <exit 0>

List remote runs:

    >>> run("guild runs list --remote guild-uat-pins")
    Refreshing run info for guild-uat-pins
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Pushing the same runs again should be a no-op:

    >>> run("guild runs push guild-uat-pins -y")
    Pushing runs to pins board...
    WARNING: Run ... already exists in pins board. Skipping.
    WARNING: Run ... already exists in pins board. Skipping.
    Refreshing run info for guild-uat-pins
    <exit 0>

    >>> run("guild runs list --remote guild-uat-pins")
    Refreshing run info for guild-uat-pins
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1
    <exit 0>

Show remote run info:

    >>> run("guild runs info --remote guild-uat-pins")
    Refreshing run info for guild-uat-pins
    id: ...
    operation: hello
    ...
    <exit 0>

Pull runs

    >>> run("guild runs delete -y")
    Deleted 2 run(s)
    <exit 0>
    >>> run("guild runs list")
    <exit 0>
    >>> run("guild runs pull guild-uat-pins -y")
    Refreshing run info for guild-uat-pins
    >>> run("guild runs list")
    [1:...]  hello  ...  completed  run-2
    [2:...]  hello  ...  completed  run-1

Delete runs from remote

    >>> run("guild runs delete --remote guild-uat-pins -y")
    Refreshing run info for guild-uat-pins
    WARNING: Deleting pins runs is always permanent. Nothing will be deleted.
    Refreshing run info for guild-uat-pins
    <exit 0>

    >>> run("guild runs delete --remote guild-uat-pins -y --permanent")
    Refreshing run info for guild-uat-pins
    Refreshing run info for guild-uat-pins
    <exit 0>

    >>> run("guild runs list --remote guild-uat-pins")
    Refreshing run info for guild-uat-pins
    <exit 0>


    