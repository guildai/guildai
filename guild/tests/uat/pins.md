# Pins remote

The pins remote type uses the
[`pins`](https://rstudio.github.io/pins-python) library to provide
backend runs storage. It supports the following Guild commands:

- runs
- runs info
- runs delete
- runs restore
- runs purge
- pull
- push

Pins remote does not support these commands:

- cat
- check
- diff
- label
- ls
- run
- stop
- watch

## Pins configuration

When configuring a pins remote, the following two attributes are
always required:

- type - must be 'pins'
- board-type - must be one of the supported board types used in Pins
  board constrution as listed in
  https://rstudio.github.io/pins-python/api/constructors (e.g. the
  `folder` corresponds to `board_folder`, etc.)

Note, however, that the `temp` board type is not supported. `temp`
boards are ephemeral and cannot be used as persistent Guild remote
stores. `folder` boards with an explicit path must be used instead.

Additional config may be required based on the specific board
constructor. Such config corresponds to the named arguments for the
applicable constructor. E.g. `path` is named argument for
`board_folder` and is therefore required when `board-type` is
'folder'.

Create a sample project to illustrate.

    >>> use_project(mkdtemp())

    >>> write("hello.py", """
    ... msg = "hello"
    ... print(msg)
    ... """)

Define a number of board types for the project in `guild-config.yml`.

    >>> pins_tmp = mkdtemp()

    >>> write("guild-config.yml", f"""
    ... remotes:
    ...   folder:
    ...     description: Folder {pins_tmp}
    ...     type: pins
    ...     board-type: folder
    ...     path: {pins_tmp}
    ...
    ...   folder-missing-config:
    ...     description: Folder with missing required config
    ...     type: pins
    ...     board-type: folder
    ...
    ...   folder-missing-path:
    ...     description: Folder with non-existing path
    ...     type: pins
    ...     board-type: folder
    ...     path: /does_not_exit
    ...
    ...   folder-rel-path:
    ...     description: Folder with relative path
    ...     type: pins
    ...     board-type: folder
    ...     path: ./rel_path
    ...
    ...   invalid-board-type:
    ...     description: Invalid board type
    ...     type: pins
    ...     board-type: not-valid
    ...
    ...   temp-board:
    ...     description: Temp board type (not supported)
    ...     type: pins
    ...     board-type: temp
    ...
    ... """)

List the remotes.

    >>> run("guild remotes")  # doctest: +REPORT_UDIFF
    folder                 pins  Folder ...
    folder-missing-config  pins  Folder with missing required config
    folder-missing-path    pins  Folder with non-existing path
    folder-rel-path        pins  Folder with relative path
    invalid-board-type     pins  Invalid board type
    temp-board             pins  Temp board type (not supported)

Use the `remote status` command to check the status of each remote.

    >>> run("guild remote status folder")
    folder (board ...) is available

    >>> run("guild remote status folder-missing-config")
    guild: remote folder-missing-config has a configuration error:
    board type 'folder' requires the following config: path
    <exit 1>

    >>> run("guild remote status folder-missing-path")
    guild: remote folder-missing-path is not available: /does_not_exit
    does not exist
    <exit 1>

    >>> run("guild remote status folder-rel-path")
    guild: remote folder-rel-path has a configuration error: folder
    paths cannot be relative (./rel_path)
    <exit 1>

    >>> run("guild remote status invalid-board-type")
    guild: remote invalid-board-type has a configuration error:
    unsupported board type 'not-valid' - refer to
    https://rstudio.github.io/pins-python/api/constructors for list
    of supported types
    <exit 1>

    >>> run("guild remote status temp-board")
    guild: remote temp-board has a configuration error: pins remote
    does not support temp boards - use a folder board pointing to a
    temp directory instead
    <exit 1>

## Run storage

The pins remote is used to store Guild runs.

The `folder` board is backed by the `pins_tmp` directory (see above
configuration). The directory is initially empty.

    >>> find(pins_tmp)
    <empty>

The `folder` remote board does not contain runs.

    >>> run("guild runs -r folder")
    Refreshing run info for folder
    <exit 0>

Generate some sample runs to store.

    >>> run("guild run hello.py msg='hello run-1' --tag red -y")
    hello run-1

    >>> run("guild run hello.py msg='hello run-2' --tag green -y")
    hello run-2

    >>> run("guild runs -s")
    [1]  hello.py  completed  green msg='hello run-2'
    [2]  hello.py  completed  red msg='hello run-1'

### Pushing runs

Push local runs to the `folder` remote.

    >>> run("guild push folder -y")
    Pushing runs to pins board
    Writing pin:
    Name: '...'
    Version: ...
    Writing pin:
    Name: '...'
    Version: ...
    Writing pin:
    Name: '...'
    Version: ...
    Writing pin:
    Name: '...'
    Version: ...
    Refreshing run info for folder
    <exit 0>

TODO: Verify that the duplicate "Writing pin" logged messages are
okay. If there's a way to control the logging where we can show
something like "Writing run xxxxx" (or similar) this would be better.

Show remote run info.

    >>> run("guild runs info 1 -r folder")  # doctest: +REPORT_UDIFF
    Refreshing run info for folder
    id: ...
    operation: hello.py
    from: ...
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: green msg='hello run-2'
    sourcecode_digest: ...
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main hello --msg "hello run-2"
    exit_status: 0
    pid:
    tags:
      - green
    flags:
      msg: hello run-2
    scalars:

    >>> run("guild runs info 2 -r folder")  # doctest: +REPORT_UDIFF
    Refreshing run info for folder
    id: ...
    operation: hello.py
    from: ...
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: red msg='hello run-1'
    sourcecode_digest: ...
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main hello --msg "hello run-1"
    exit_status: 0
    pid:
    tags:
      - red
    flags:
      msg: hello run-1
    scalars:

### Push and existing runs

Push to the remote again. Pins skips existing runs.

    >>> run("guild push folder -y")
    Pushing runs to pins board
    Run ... already exists in pins board, skipping
    Run ... already exists in pins board, skipping
    Refreshing run info for folder
    <exit 0>

TODO: This is not really the way remotes should work... consider
runs-in-progress that one might want to push before they complete. It
may be that these re-pushes should create pin versions, assuming pins
are immutable. Otherwise they should probably outright replace
existing runs. An optimization here might be to generate a digest for
the run dir and store it with the pin metadata - and re-push if that
digest changes. We can't even rely on run status here as a run can be
restarted.

    >>> run("guild runs -s -r folder")
    Refreshing run info for folder
    [1]  hello.py  completed  green msg='hello run-2'
    [2]  hello.py  completed  red msg='hello run-1'

### Pulling runs

Pull from the remote.

    >>> run("guild pull folder -y")
    Refreshing run info for folder
    <exit 0>

TODO: Note something here? ^^^

    >>> run("guild runs -s")
    [1]  hello.py  completed  green msg='hello run-2'
    [2]  hello.py  completed  red msg='hello run-1'

Delete the local runs to confirm we can restore them.

    >>> run("guild runs rm -y")
    Deleted 2 run(s)

    >>> run("guild runs -s")
    <exit 0>

Pull the remote runs.

    >>> run("guild pull folder -y")
    Refreshing run info for folder
    <exit 0>

TODO: something's definitely happening here that we want to show ^^^

    >>> run("guild runs -s")
    [1]  hello.py  completed  green msg='hello run-2'
    [2]  hello.py  completed  red msg='hello run-1'

### Deleting remote runs

Delete runs from the remote.

    >>> run("guild runs rm -r folder -y")
    Refreshing run info for folder
    WARNING: Deleting pins runs is always permanent. Nothing will be deleted.
    Refreshing run info for folder

TODO: The command should fail early unless `-p` is used.

    >>> run("guild runs -s -r folder")
    Refreshing run info for folder
    [1]  hello.py  completed  green msg='hello run-2'
    [2]  hello.py  completed  red msg='hello run-1'

To delet the pins we need to specify the `--permanent` option.

    >>> run("guild runs rm -p -r folder -y")
    Refreshing run info for folder
    Refreshing run info for folder
    <exit 0>

TODO: See if we can avoid this duplication ^^^

    >>> run("guild runs -s -r folder")
    Refreshing run info for folder
    <exit 0>

<!-- Pull runs -->

<!--     >> run("guild runs delete -y") -->
<!--     Deleted 2 run(s) -->
<!--     <exit 0> -->
<!--     >> run("guild runs list") -->
<!--     <exit 0> -->
<!--     >> run("guild runs pull guild-uat-pins -y") -->
<!--     Refreshing run info for guild-uat-pins -->
<!--     >> run("guild runs list") -->
<!--     [1:...]  hello  ...  completed  run-2 -->
<!--     [2:...]  hello  ...  completed  run-1 -->

<!-- Delete runs from remote -->

<!--     >> run("guild runs delete --remote guild-uat-pins -y") -->
<!--     Refreshing run info for guild-uat-pins -->
<!--     WARNING: Deleting pins runs is always permanent. Nothing will be deleted. -->
<!--     Refreshing run info for guild-uat-pins -->
<!--     <exit 0> -->

<!--     >> run("guild runs delete --remote guild-uat-pins -y --permanent") -->
<!--     Refreshing run info for guild-uat-pins -->
<!--     Refreshing run info for guild-uat-pins -->
<!--     <exit 0> -->

<!--     >> run("guild runs list --remote guild-uat-pins") -->
<!--     Refreshing run info for guild-uat-pins -->
<!--     <exit 0> -->



## Unsupported commands for pins

    >>> run("guild check -r folder")
    guild: remote 'folder' does not support this operation
    <exit 1>

    >>> run("guild stop -r folder")
    guild: remote 'folder' does not support this operation
    <exit 1>

    >>> run("guild watch -r folder")
    guild: remote 'folder' does not support this operation
    <exit 1>

    >>> run("guild ls -r folder")
    guild: remote 'folder' does not support this operation
    <exit 1>

    >>> run("guild diff -r folder")
    guild: remote 'folder' does not support this operation
    <exit 1>

    >>> run("guild cat --output -r folder")
    guild: remote 'folder' does not support this operation
    <exit 1>

    >>> run("guild label --set xxx -r folder -y")
    guild: remote 'folder' does not support this operation
    <exit 1>

To verify that `run` is not supported, we need to create a
remote-runaable operation.

    >>> write("guild.yml", """
    ... hello: {}
    ... """)

    >>> run("guild run hello -r folder -y")
    guild: remote 'folder' does not support this operation
    <exit 1>
