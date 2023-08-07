# archive command

Guild 0.9.1 introduces an `archive` command.

- Used to archive runs under Guild home
- Similar to `export` but works with named archives

To illustrate, create an ephemeral project.

    >>> use_project(mkdtemp())

Create a local `.guild` directory to use as Guild home.

    >>> mkdir(".guild")
    >>> set_guild_home(abspath(".guild"))

Create `config.yml` in Guild home. This tells Guild where to look for
archives.

    >>> touch(path(".guild", "config.yml"))

List available archives.

    >>> run("guild archive --list")
    <exit 0>

Create a sample script.

    >>> write("test.py", """
    ... msg = "hello"
    ... print(msg)
    ... """)

Create some runs.

    >>> run("guild run test.py -y")
    hello

    >>> run("guild run test.py msg=hi -y")
    hi

    >>> run("guild runs -s")
    [1]  test.py  completed  msg=hi
    [2]  test.py  completed  msg=hello

Attempt to archive the runs to a non-existing archive.

    >>> run("guild archive 'My archive' -y")
    guild: archive 'My archive' does not exist
    Try 'guild archive --list' to list available archives or
    use the '--create' option.
    <exit 1>

Run the same command with `--create`.

    >>> run("guild archive 'My archive' --create -y")
    Creating 'My archive'
    Moving ...
    Moving ...
    Archived 2 run(s) to 'My archive'

By default Guild moves runs from the repository to the archive.

    >>> run("guild runs -s")
    <exit 0>

List runs in 'My archive'.

    >>> run("guild runs --archive 'My archive' -s")
    [1]  test.py  completed  msg=hi
    [2]  test.py  completed  msg=hello

List archives.

    >>> run("guild archive --list")
    My archive

The archive path is included when '--vervose' is used with '--list'.

    >>> run("guild archive --list --verbose")
    My archive
      path: ...
    <exit 0>

We can move the archived runs back into the repository using `import`.

    >>> run("guild import 'My archive' --move -y")
    Moving ...
    Moving ...
    Imported 2 run(s) from My archive

    >>> run("guild runs --archive 'My archive' -s")
    <exit 0>

    >>> run("guild runs -s")
    [1]  test.py  completed  msg=hi
    [2]  test.py  completed  msg=hello

Archive the runs again, this time copying them rather than moving.

    >>> run("guild archive 'My archive' --copy -y")
    Copying ...
    Copying ...
    Archived 2 run(s) to 'My archive'

    >>> run("guild runs -s")
    [1]  test.py  completed  msg=hi
    [2]  test.py  completed  msg=hello

    >>> run("guild runs --archive 'My archive' -s")
    [1]  test.py  completed  msg=hi
    [2]  test.py  completed  msg=hello

Guild does not replace runs on archive or import.

    >>> run("guild archive 'My archive' -y")
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    Archived 0 run(s) to 'My archive'

    >>> run("guild import 'My archive' -y")
    WARNING: ... exists, skipping
    WARNING: ... exists, skipping
    Imported 0 run(s) from My archive

Delete runs from an archive using '--archive' with the delete command.

    >>> run("guild runs delete -A 'My archive' -y")
    Deleted 2 run(s)

Using '--create' on an existing archive does not create a new
archive. Guild uses the existing archive.

    >>> run("guild archive 'My archive' --copy --create -y")
    Copying ...
    Copying ...
    Archived 2 run(s) to 'My archive'

When creating a new archive, use '--description' to set a description
for the new archive. This appears in the listing.

    >>> run("guild archive 'Second archive' --create "
    ...     "--description 'Another place for runs' -y")
    Creating 'Second archive'
    Moving ...
    Moving ...
    Archived 2 run(s) to 'Second archive'

    >>> run("guild archive --list")
    My archive
    Second archive  Another place for runs
