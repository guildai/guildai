# Export / Import Using Zip Archives

These tests illustrate basic export/import features.

We use use the hello example to generate runs.

    >>> cd(example("hello"))

Delete existing runs for test.

    >>> quiet("guild runs rm -y")

Generate three runs:

    >>> run("guild run msg=[hello,hi,hola] -y")
    INFO: [guild] Running trial ...: hello (msg=hello)
    hello
    INFO: [guild] Running trial ...: hello (msg=hi)
    hi
    INFO: [guild] Running trial ...: hello (msg=hola)
    hola
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    <exit 0>

## Export with Copy (default)

Create a temp dir to write our archive to.

    >>> archive = path(mkdtemp(), "runs.zip")

Show preview:

    >>> run("guild export %s 1" % archive, timeout=2)
    You are about to copy the following runs to '...':
      [...]  hello   ...  completed  msg=hola
    Continue? (Y/n)
    <exit ...>

Export (copies):

    >>> run("guild export %s 1 -y" % archive)
    Copying ...
    Exported 1 run(s) to .../runs.zip
    <exit 0>

Directories in export dir:

    >>> run("python -m zipfile -l %s" % archive)
    File Name    Modified         Size
    .../              ...            0
    .../.guild/       ...            0
    ...

List runs in archive:

    >>> run("guild runs -A %s" % archive)
    [1:...]  hello   ...  completed  msg=hola
    <exit 0>

Runs still exist because the default export mode is to copy runs.

    >>> run("guild runs")
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    <exit 0>

Export two more runs - preview.

    >>> run("guild export %s 2 3" % archive, timeout=2)
    You are about to copy the following runs to '...':
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
    Continue? (Y/n)
    <exit ...>

Export the runs:

    >>> run("guild export %s 2 3 -y" % archive)
    Copying ...
    Copying ...
    Exported 2 run(s) to .../runs.zip
    <exit 0>

List runs in archive:

    >>> run("guild runs -A %s" % archive)
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    <exit 0>

## Overwriting Export Runs

Guild won't overwrite runs in an archive.

    >>> run("guild export %s -y" % archive)
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    Exported 0 run(s) to ...
    <exit 0>

## Export with Move

Export to another export dir using the `--move` option:

    >>> archive = path(mkdtemp(), "runs.zip")

Preview:

    >>> run("guild export %s --move" % archive, timeout=2)
    You are about to move the following runs to '...':
      [...]  hello   ...  completed  msg=hola
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
    Continue? (Y/n)
    <exit ...>

Export with move:

    >>> run("guild export %s --move -y" % archive)
    Moving ...
    Moving ...
    Moving ...
    Exported 3 run(s) to ...
    <exit 0>

Archive contents:

    >>> run("python -m zipfile -l %s" % archive)
    File Name    Modified         Size
    .../              ...            0
    .../.guild/       ...            0
    ...

List runs in archive:

    >>> run("guild runs -A %s" % archive)
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    <exit 0>

Current runs are empty because runs were moved rather than copied.

    >>> run("guild runs")
    <exit 0>

## Import with Copy (default)

Import preview:

    >>> run("guild import %s" % archive, timeout=2)
    You are about to import (copy) the following runs from '...':
      [...]  hello   ...  completed  msg=hola
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
    Continue? (Y/n)
    <exit ...>

Import runs:

    >>> run("guild import %s -y" % archive)
    Copying ...
    Copying ...
    Copying ...
    Imported 3 run(s) from ...
    <exit 0>

Current runs:

    >>> run("guild runs")
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    <exit 0>

## Overwriting Runs on Import

Import again:

    >>> run("guild import %s -y" % archive)
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    Imported 0 run(s) from ...
    <exit 0>

## Import with Move - no supported for zip archives

    >>> run("guild import %s --move" % archive, timeout=2)
    guild: '--move' cannot be used with zip archives
    <exit 1>

## Errors

Looks like an zip file but isn't:

    >>> archive = path(mkdtemp(), "run.zip")
    >>> touch(archive)

    >>> run("guild export %s -y" % archive)
    guild: cannot write to .../run.zip: File is not a zip file
    <exit 1>

    >>> run("guild import %s -y" % archive)
    ERROR: cannot read from .../run.zip: File is not a zip file
    No runs to import.
    <exit 0>
