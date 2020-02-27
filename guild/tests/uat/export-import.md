# Export / Import

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
    [4:...]  hello+  ...  completed
    <exit 0>

## Export with Copy (default)

Create an export dir:

    >>> export_dir = mkdtemp()

Show preview:

    >>> run("guild export %s" % export_dir, timeout=2)
    You are about to copy the following runs to '...':
      [...]  hello   ...  completed  msg=hola
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
      [...]  hello+  ...  completed
    Continue? (Y/n)
    <exit ...>

Export with copy:

    >>> run("guild export %s -y" % export_dir)
    Copying ...
    Copying ...
    Copying ...
    Copying ...
    Exported 4 run(s)
    <exit 0>

Directories in export dir:

    >>> dir(export_dir)
    ['.guild-nocopy',
     '...',
     '...',
     '...',
     '...']

Current runs still exist because the default export mode is to copy
runs.

    >>> run("guild runs")
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    [4:...]  hello+  ...  completed
    <exit 0>

## Overwriting Export Runs

Guild won't overwrite runs in an export.

    >>> run("guild export %s -y" % export_dir)
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    Exported 0 run(s)
    <exit 0>

## Export with Move

Export to another export dir using the `--move` option:

    >>> export_dir = mkdtemp()

Preview:

    >>> run("guild export %s --move" % export_dir, timeout=2)
    You are about to move the following runs to '...':
      [...]  hello   ...  completed  msg=hola
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
      [...]  hello+  ...  completed
    Continue? (Y/n)
    <exit ...>

Export with move:

    >>> run("guild export %s --move -y" % export_dir)
    Moving ...
    Moving ...
    Moving ...
    Moving ...
    Exported 4 run(s)
    <exit 0>

Export dir:

    >>> dir(export_dir)
    ['.guild-nocopy',
     '...',
     '...',
     '...',
     '...']

Current runs are empty because runs were moved rather than copied.

    >>> run("guild runs")
    <exit 0>

## Import with Copy (default)

Import preview:

    >>> run("guild import %s" % export_dir, timeout=2)
    You are about to import (copy) the following runs from '...':
      [...]  hello   ...  completed  msg=hola
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
      [...]  hello+  ...  completed
    Continue? (Y/n)
    <exit ...>

Import runs:

    >>> run("guild import %s -y" % export_dir)
    Copying ...
    Copying ...
    Copying ...
    Copying ...
    Imported 4 run(s)
    <exit 0>

Current runs:

    >>> run("guild runs")
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    [4:...]  hello+  ...  completed
    <exit 0>

## Overwriting Runs on Import

Import again:

    >>> run("guild import %s -y" % export_dir)
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    Imported 0 run(s)
    <exit 0>

## Import with Move

Delete existing runs:

    >>> quiet("guild runs rm -y")

Import preview:

    >>> run("guild import %s --move" % export_dir, timeout=2)
    You are about to import (move) the following runs from '...':
      [...]  hello   ...  completed  msg=hola
      [...]  hello   ...  completed  msg=hi
      [...]  hello   ...  completed  msg=hello
      [...]  hello+  ...  completed
    Continue? (Y/n)
    <exit ...>

Import runs:

    >>> run("guild import %s -y" % export_dir)
    Copying ...
    Copying ...
    Copying ...
    Copying ...
    Imported 4 run(s)
    <exit 0>

Current runs:

    >>> run("guild runs")
    [1:...]  hello   ...  completed  msg=hola
    [2:...]  hello   ...  completed  msg=hi
    [3:...]  hello   ...  completed  msg=hello
    [4:...]  hello+  ...  completed
    <exit 0>

## Errors

Directory structure to test errors:

    >>> tmpdir = mkdtemp()
    >>> touch(path(tmpdir, "a-file"))

Invalid export location:

    >>> run("guild export %s/a-file -y" % tmpdir)
    guild: '.../a-file' is not a directory
    <exit 1>

Import non-existing archive:

    >>> run("guild import %s/missing-dir -y" % tmpdir)
    guild: archive '.../missing-dir' does not exist
    <exit 1>

Import a file rather than a directory:

    >>> run("guild import %s/a-file -y" % tmpdir)
    guild: invalid archive '.../a-file' - expected a directory
    <exit 1>
