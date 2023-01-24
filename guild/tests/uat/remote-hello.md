# Remote hello tests

These tests exercise a full range of remote commands using the `hello`
example project.

Ensure all remote runs are deleted:

    >>> quiet("guild runs rm -r guild-uat -y")

    >>> run("guild runs -r guild-uat")
    <exit 0>

These tests run various hello operations remotely.

## Generate runs

### `hello-package`

Run operations from the `hello-package` example project.

    >>> cd(example("hello-package"))

Run `hello`:

    >>> run("guild run hello -r guild-uat -y")
    Building package
    ...
    Installing package and its dependencies
    Processing ./gpkg.hello-0.1-py2.py3-none-any.whl
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    Starting hello on guild-uat as ...
    Hello Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>

Run `hello-file`:

    >>> run("guild run hello-file file=hello-2.txt -r guild-uat -y")
    Building package
    ...
    Installing package and its dependencies
    Processing ./gpkg.hello-0.1-py2.py3-none-any.whl
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    Starting hello-file on guild-uat as ...
    Resolving packaged-files
    Reading message from hello-2.txt
    Hello, from a 2nd file!
    <BLANKLINE>
    Saving message to msg.out
    Run ... stopped with a status of 'completed'
    <exit 0>

Run `hello-op`:

    >>> run("guild run hello-op -r guild-uat -y")
    Getting run info on guild-uat
    Building package
    ...
    Installing package and its dependencies
    Processing ./gpkg.hello-0.1-py2.py3-none-any.whl
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    Starting hello-op on guild-uat as ...
    Resolving op
    Using run ... for op
    Reading message from msg.out
    Hello, from a 2nd file!
    <BLANKLINE>
    Run ... stopped with a status of 'completed'
    <exit 0>

### `hello-package-2`

Run operations from the `hello-package-2` example project.

    >>> cd(example("hello-package-2"))

Run `hello`:

    >>> run("guild run hello -r guild-uat -y")
    Building package
    ...
    Installing package and its dependencies
    Processing ./gpkg.hello-0.1-py2.py3-none-any.whl
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    Starting hello on guild-uat as ...
    Hello Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>

Run `hello-file`:

    >>> run("guild run hello-file -r guild-uat -y")
    Building package
    ...
    Installing package and its dependencies
    Processing ./gpkg.hello-0.1-py2.py3-none-any.whl
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    Starting hello-file on guild-uat as ...
    Resolving packaged-files
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    Run ... stopped with a status of 'completed'
    <exit 0>

Run `hello-op`:

    >>> run("guild run hello-op -r guild-uat -y")
    Getting run info on guild-uat
    Building package
    ...
    Installing package and its dependencies
    Processing ./gpkg.hello-0.1-py2.py3-none-any.whl
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    Starting hello-op on guild-uat as ...
    Resolving op
    Using run ... for op
    Reading message from msg.out
    Hello, from a file!
    <BLANKLINE>
    Run ... stopped with a status of 'completed'
    <exit 0>

## List runs

List remote runs.

    >>> run("guild runs list -s --remote guild-uat -s")
    [1]  gpkg.hello/hello-op    completed  op=...
    [2]  gpkg.hello/hello-file  completed  file=hello.txt
    [3]  gpkg.hello/hello       completed  msg='Hello Guild!'
    [4]  gpkg.hello/hello-op    completed  op=...
    [5]  gpkg.hello/hello-file  completed  file=hello-2.txt
    [6]  gpkg.hello/hello       completed  msg='Hello Guild!'

Filter by completedd status.

    >>> run("guild runs list --completed -r guild-uat -s")
    [1]  gpkg.hello/hello-op    completed  op=...
    [2]  gpkg.hello/hello-file  completed  file=hello.txt
    [3]  gpkg.hello/hello       completed  msg='Hello Guild!'
    [4]  gpkg.hello/hello-op    completed  op=...
    [5]  gpkg.hello/hello-file  completed  file=hello-2.txt
    [6]  gpkg.hello/hello       completed  msg='Hello Guild!'

    >>> run("guild runs list --not-completed -r guild-uat -s")
    <exit 0>

Filter by terminated status.

    >>> run("guild runs list -St -r guild-uat -s")
    <exit 0>

Filter by operation name.

    >>> run("guild runs -Fo hello -s -r guild-uat")
    [1]  gpkg.hello/hello  completed  msg='Hello Guild!'
    [2]  gpkg.hello/hello  completed  msg='Hello Guild!'

Filter by multiple operation names.

    >>> run("guild runs -Fo hello-file -Fo hello -s -r guild-uat")
    [1]  gpkg.hello/hello-file  completed  file=hello.txt
    [2]  gpkg.hello/hello       completed  msg='Hello Guild!'
    [3]  gpkg.hello/hello-file  completed  file=hello-2.txt
    [4]  gpkg.hello/hello       completed  msg='Hello Guild!'

Filter by partial name match (no matches).

    >>> run("guild runs -Fo hello/hello -s -r guild-uat")
    <exit 0>

Filter by full name.

    >>> run("guild runs -Fo gpkg.hello/hello-op -s -r guild-uat")
    [1]  gpkg.hello/hello-op  completed  op=...
    [2]  gpkg.hello/hello-op  completed  op=...

Filter by package name.

    >>> run("guild runs -Fo gpkg.hello/ -s -r guild-uat")
    [1]  gpkg.hello/hello-op    completed  op=...
    [2]  gpkg.hello/hello-file  completed  file=hello.txt
    [3]  gpkg.hello/hello       completed  msg='Hello Guild!'
    [4]  gpkg.hello/hello-op    completed  op=...
    [5]  gpkg.hello/hello-file  completed  file=hello-2.txt
    [6]  gpkg.hello/hello       completed  msg='Hello Guild!'

Filter by expression.

    >>> run("guild runs -F 'label contains Hello' -s -r guild-uat")
    [1]  gpkg.hello/hello-file  completed  file=hello.txt
    [2]  gpkg.hello/hello       completed  msg='Hello Guild!'
    [3]  gpkg.hello/hello-file  completed  file=hello-2.txt
    [4]  gpkg.hello/hello       completed  msg='Hello Guild!'

## List run files

These tests run various versions of the `ls` command to show files
for the latest run.

`ls` is generated from the run manfiest.

    >>> run("guild cat -p .guild/manifest -r guild-uat")  # doctest: +REPORT_UDIFF
    s README.md 60eb176260122f67440d8cea65f7dc86b8331b9c README.md
    s guild.yml 3f8bc75baa61cad67c2d596b353f3b3f3ba2fbd0 guild.yml
    s data/hello-2.txt 3c22f452dc3a375d0d35a832ba0bf5cbb79b553f data/hello-2.txt
    s data/hello.txt 7e1a1a698162c39e88d7855ccd0d73bfa72db1a1 data/hello.txt
    s hello/__init__.py da39a3ee5e6b4b0d3255bfef95601890afd80709 hello/__init__.py
    s hello/cat.py 51d27379080c44b20d868246bd6981884e820be5 hello/cat.py
    s hello/say.py 52dc1bf9d9017c3cb56530ad70d3f1bb84b1974e hello/say.py
    d msg.out 7e1a1a698162c39e88d7855ccd0d73bfa72db1a1 operation:hello-file

Show default files list.

    >>> run("guild ls -r guild-uat -n", ignore=["__pycache__"])  # doctest: +REPORT_UDIFF
    README.md
    data/
    data/hello-2.txt
    data/hello.txt
    guild.yml
    hello/
    hello/__init__.py
    hello/cat.py
    hello/say.py
    msg.out

Show source code files.

    >>> run("guild ls -r guild-uat -n --sourcecode")  # doctest: +REPORT_UDIFF
    README.md
    data/hello-2.txt
    data/hello.txt
    guild.yml
    hello/__init__.py
    hello/cat.py
    hello/say.py

    >>> run("guild ls -r guild-uat -n --dependencies")
    msg.out

    >>> run("guild ls -r guild-uat -n --generated", ignore=["__pycache__"])
    <exit 0>

    >>> run("guild ls -r guild-uat --all -n", ignore=["__pycache__"]) # doctest: +REPORT_UDIFF
    .guild/
    .guild/attrs/
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/env
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/label
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/job-packages/...
    .guild/manifest
    .guild/opref
    .guild/output
    .guild/output.index
    README.md
    data/
    data/hello-2.txt
    data/hello.txt
    guild.yml
    hello/
    hello/__init__.py
    hello/cat.py
    hello/say.py
    msg.out

## Runs info

Show run information for the latest run.

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    from: gpkg.hello==0.1
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: op=...
    sourcecode_digest: ...
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main hello.cat --
    exit_status: 0
    pid:
    tags:
    flags:
      op: ...
    scalars:
    <exit 0>

Include manifest in output.

    >>> run("guild runs info -m -r guild-uat")
    id: ...
    ...
    manifest:
      dependencies:
        - msg.out
      sourcecode:
        - README.md
        - data/hello-2.txt
        - data/hello.txt
        - guild.yml
        - hello/__init__.py
        - hello/cat.py
        - hello/say.py
    <exit 0>

## Show file contents

Use `cat` to show the contents of a remote file.

    >>> run("guild cat -r guild-uat -p msg.out")
    Hello, from a file!
    <exit 0>

    >>> run("guild cat -r guild-uat --output")
    Reading message from msg.out
    Hello, from a file!

    >>> run("guild cat -r guild-uat --sourcecode -p hello/say.py")
    msg = "Hello Guild!"
    <BLANKLINE>
    print(msg)

## Remote diffing

Verify that a whole-run diff runs without error.

    >>> quiet("guild diff --remote guild-uat -c 'diff -ur'")

Compare various run content for the two `hello-file` runs.

    >>> run("guild diff -Fo hello-file --flags -r guild-uat -c 'diff -ur'")
    --- .../attrs/flags ...
    +++ .../attrs/flags ...
    @@ -1 +1 @@
    -file: hello-2.txt
    +file: hello.txt

    >>> run("guild diff -Fo hello-file -p msg.out -r guild-uat -c 'diff -ur'")
    --- .../msg.out ...
    +++ .../msg.out ...
    @@ -1 +1 @@
    -Hello, from a 2nd file!
    +Hello, from a file!
    <exit 0>

    >>> run("guild diff -Fo hello-file --output -r guild-uat -c 'diff -ur'")
    --- .../.guild/output ...
    +++ .../.guild/output ...
    @@ -1,4 +1,4 @@
    -Reading message from hello-2.txt
    -Hello, from a 2nd file!
    +Reading message from hello.txt
    +Hello, from a file!
    <BLANKLINE>
     Saving message to msg.out
    <exit 0>

## Watch last remote hello op

The `watch` command watches running operation. This test shows the
error message that Guild displays when there is no running operation.

First, list any running ops.

    >>> run("guild runs --running --remote guild-uat")
    <exit 0>

Try to watch an operation.

    >>> run("guild watch --remote guild-uat")
    guild: nothing to watch
    You can view the output of a specific run using 'guild watch RUN'.
    <exit 1>

## Stop last remote hello op

The `stop` command attempts to stop a running operation. These show
the error message when there are no running operations to stop.

List running operations.

    >>> run("guild runs --running --remote guild-uat")
    <exit 0>

Try to stop runs.

    >>> run("guild stop --remote guild-uat")
    Nothing to stop.
    <exit 0>

## Label remote runs

Set a label.

    >>> run("guild label 1 -s remote-run-123 -r guild-uat -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs -s -r guild-uat -n1")
    [1]  gpkg.hello/hello-op  completed  remote-run-123
    <exit 0>

Tag (prepend) a value to a label.

    >>> run("guild label --prepend foo 1 -r guild-uat -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs -s -r guild-uat -n1")
    [1]  gpkg.hello/hello-op  completed  foo remote-run-123
    <exit 0>

Append a value to a label.

    >>> run("guild label --append bar 1 -r guild-uat -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs -s -r guild-uat -n1")
    [1]  gpkg.hello/hello-op  completed  foo remote-run-123 bar
    <exit 0>

Clear label for run 1.

    >>> run("guild label --clear 1 -r guild-uat -y")
    Cleared label for 1 run(s)
    <exit 0>

    >>> run("guild runs -s -r guild-uat -n1")
    [1]  gpkg.hello/hello-op  completed
    <exit 0>

Restore the original label using append.

    >>> run("guild label -a remote-run-123 -r guild-uat -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs -s -r guild-uat -n1")
    [1]  gpkg.hello/hello-op  completed  remote-run-123
    <exit 0>

## Tag remote runs

The latest run is not tagged.

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    tags:
    ...
    <exit 0>

Save the run label (we restore it later).

    >>> label_save = run_capture("guild select --attr label -r guild-uat")

Add two tags with label sync.

    >>> run("guild tag -a blue -a green --sync-labels -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs -s -r guild-uat -n1")
    [1]  gpkg.hello/hello-op  completed  blue green remote-run-123
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: blue green remote-run-123
    ...
    tags:
      - blue
      - green
    ...
    <exit 0>

    >>> run("guild tag --list-all -r guild-uat")
    blue
    green
    <exit 0>

Delete two tags, one non-existing.

    >>> run("guild tag -d blue -d yellow -s -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: green remote-run-123
    ...
    tags:
      - green
    ...
    <exit 0>

    >>> run("guild tag --list-all -r guild-uat")
    green
    <exit 0>

Delete an existing tag, add a new tag.

    >>> run("guild tag -d green -a orange -s -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: orange remote-run-123
    ...
    tags:
      - orange
    ...
    <exit 0>

    >>> run("guild tag --list-all -r guild-uat")
    orange
    <exit 0>

Clear tags and add a new tag.

    >>> run("guild tag -c -a cyan -s -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: cyan remote-run-123
    ...
    tags:
      - cyan
    ...
    <exit 0>

    >>> run("guild tag --list-all -r guild-uat")
    cyan
    <exit 0>

Clear all tags without label sync.

    >>> run("guild tag -c -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: cyan remote-run-123
    ...
    tags:
    ...
    <exit 0>

    >>> run("guild tag --list-all -r guild-uat")
    <exit 0>

Reset the label.

    >>> run(f"guild label --set '{label_save}' -r guild-uat -y")
    Labeled 1 run(s)

## Remote comment hello

The latest run has no comments.

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
    <exit 0>

Add a comment.

    >>> run("guild comment -a 'A nice comment.' -r guild-uat -y")
    Added comment to 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
    [1] ... ...-...-... ...:...:...
    <BLANKLINE>
      A nice comment.
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
      -
        body: A nice comment.
        host: ...
        time: ...
        user: ...
    <exit 0>

Add another comment.

    >>> run("guild comment -a 'A second comment.' -r guild-uat -y")
    Added comment to 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
    [1] ...
    <BLANKLINE>
      A nice comment.
    <BLANKLINE>
    [2] ...
    <BLANKLINE>
      A second comment.
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
      -
        body: A nice comment.
        host: ...
        time: ...
        user: ...
      -
        body: A second comment.
        host: ...
        time: ...
        user: ...
    <exit 0>

Filter runs by comment.

    >>> run("guild runs --comments -s -Fc nice -r guild-uat")
    [1]  gpkg.hello/hello-op completed  remote-run-123
      ...
    <BLANKLINE>
        A nice comment.
    <BLANKLINE>
      ...
    <BLANKLINE>
        A second comment.

    [1]  gpkg.hello/hello-op  completed  remote-run-123
    <exit 0>

    >>> run("guild runs -s -Fc second -r guild-uat")
    [1]  gpkg.hello/hello-op  completed  remote-run-123
    <exit 0>

    >>> run("guild runs -Fc 'no match' -r guild-uat")
    <exit 0>

Delete the first comment.

    >>> run("guild comment --delete 1 -r guild-uat -y")
    Deleted comment for 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
    [1] ...
    <BLANKLINE>
      A second comment.
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
      -
        body: A second comment.
        host: ...
        time: ...
        user: ...
    <exit 0>

Clear all comments.

    >>> run("guild comment --clear -r guild-uat -y")
    Deleted all comments for 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
      <no comments>
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
    <exit 0>

## Pull from remote server

Delete local runs in prep for these tests.

    >>> quiet("guild runs rm -y")

    >>> run("guild runs")
    <exit 0>

Preview a `pull` command for the remote.

    >>> run("guild pull guild-uat", timeout=5)
    Getting run info on guild-uat
    You are about to copy (pull) the following runs from guild-uat:
      [...]  gpkg.hello/hello-op    ...  completed  remote-run-123
      [...]  gpkg.hello/hello-file  ...  completed  file=hello.txt
      [...]  gpkg.hello/hello       ...  completed  msg='Hello Guild!'
      [...]  gpkg.hello/hello-op    ...  completed  op=...
      [...]  gpkg.hello/hello-file  ...  completed  file=hello-2.txt
      [...]  gpkg.hello/hello       ...  completed  msg='Hello Guild!'
    Continue? (Y/n)
    <exit -9>

    Getting run info on guild-uat
    You are about to copy (pull) the following runs from guild-uat:
      [...]  gpkg.hello/hello-op    ...  completed  remote-run-123
      [...]  gpkg.hello/hello-file  ...  completed  file=hello.txt
    Continue? (Y/n)
    <exit -9>

Run `pull`.

    >>> run("guild pull guild-uat -y")
    Getting run info on guild-uat
    ...
    <exit 0>

Show local runs.

    >>> run("guild runs -s")
    [1]  gpkg.hello/hello-op    completed  remote-run-123
    [2]  gpkg.hello/hello-file  completed  file=hello.txt
    [3]  gpkg.hello/hello       completed  msg='Hello Guild!'
    [4]  gpkg.hello/hello-op    completed  op=...
    [5]  gpkg.hello/hello-file  completed  file=hello-2.txt
    [6]  gpkg.hello/hello       completed  msg='Hello Guild!'

## Comment and push

Add a comment to run 2.

    >>> run("guild comment --add 'Nothing to see here' 2 -y")
    Added comment to 1 run(s)
    <exit 0>

Push all of the runs back to remote. Only the changes are pushed.

    >>> run("guild push guild-uat -y")
    Copying ...
    sending incremental file list
    ...
    <exit 0>

View comments for run 2 on the remote.

    >>> run("guild comment --list 2 --remote guild-uat")
    ???  gpkg.hello/hello-file  ...  completed  file=hello.txt
    [1] ...
    <BLANKLINE>
      Nothing to see here
    <BLANKLINE>
    <exit 0>
