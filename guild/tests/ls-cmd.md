---
doctest: -WINDOWS
---

# ls command

The `ls` command is used to list run files. We use the `ls` project to
generate runs we can test the `ls` command with.

    >>> project = Project(sample("projects", "ls"))

Generate a run. We revert disabling of pip freeze to verify it's
created.

    >>> with Env({"NO_PIP_FREEZE": "0"}):
    ...     project.run("make_fs.py", run_id="aaaa")

    >>> project.list_runs()
    [<guild.run.Run 'aaaa'>]

Helper function to run Guild commands for project runs.

    >>> def guild_run(cmd, ignore=None):
    ...     run("guild -H %s %s" % (project.guild_home, cmd), ignore=ignore)

By default ls prints all non-Guild files without following links.

    >>> guild_run("ls")
    ???/runs/aaaa:
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/
    <exit 0>

The directory header can be dropped with `-n, --no-format`.

    >>> guild_run("ls -n")
    a
    b
    c/
    c/d.txt
    c/e.txt
    c/f.bin
    l/
    <exit 0>

By default, Guild does not follow links in lists. Use `-L,
--follow-links` to follow links.

    >>> guild_run("ls --follow-links")
    ???/runs/aaaa:
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/
      l/d.txt
      l/e.txt
      l/f.bin
    <exit 0>

Show the full path for a list with `--full-path`.

    >>> guild_run("ls --full-path")
    ???/runs/aaaa/a
    .../runs/aaaa/b
    .../runs/aaaa/c
    .../runs/aaaa/c/d.txt
    .../runs/aaaa/c/e.txt
    .../runs/aaaa/c/f.bin
    .../runs/aaaa/l
    <exit 0>

List all files with `--all`.

    >>> guild_run("ls --all")  # doctest: +REPORT_UDIFF
    ???/runs/aaaa:
      .foo/
      .foo/.bar
      .foo/baz
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
      .guild/attrs/op
      .guild/attrs/pip_freeze
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/sourcecode_digest
      .guild/attrs/started
      .guild/attrs/stopped
      .guild/attrs/user
      .guild/attrs/user_flags
      .guild/opref
      .guild/output
      .guild/output.index
      .guild/some-guild-file
      .guild/sourcecode/
      .guild/sourcecode/README.md
      .guild/sourcecode/guild.yml
      .guild/sourcecode/make_fs.py
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/
    <exit 0>

If `--path` wants a hidden file, it's included.

    >>> guild_run("ls --path .guild")  # doctest: +REPORT_UDIFF
    ???/runs/aaaa:
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
      .guild/attrs/op
      .guild/attrs/pip_freeze
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/sourcecode_digest
      .guild/attrs/started
      .guild/attrs/stopped
      .guild/attrs/user
      .guild/attrs/user_flags
      .guild/opref
      .guild/output
      .guild/output.index
      .guild/some-guild-file
      .guild/sourcecode/
      .guild/sourcecode/README.md
      .guild/sourcecode/guild.yml
      .guild/sourcecode/make_fs.py
    <exit 0>

    >>> guild_run("ls --path .foo -n")
    .foo/
    .foo/baz
    <exit 0>

A path must match a directory or fully match the name.

    >>> guild_run("ls --path .fo -n")
    <BLANKLINE>
    <exit 0>

You can use a wildcard to match partial paths.

    >>> guild_run("ls --path .fo* -n")
    .foo/
    .foo/baz
    <exit 0>

Note that the wildcard matches hidden files in this case. This is
different from bash directory listings, which would not list hidden
files unless the pattern started with a dot.

Follow links applies to `--all`.

    >>> guild_run("ls --all -L")  # doctest: +REPORT_UDIFF
    ???/runs/aaaa:
      .foo/
      .foo/.bar
      .foo/baz
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
      .guild/attrs/op
      .guild/attrs/pip_freeze
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/sourcecode_digest
      .guild/attrs/started
      .guild/attrs/stopped
      .guild/attrs/user
      .guild/attrs/user_flags
      .guild/opref
      .guild/output
      .guild/output.index
      .guild/some-guild-file
      .guild/sourcecode/
      .guild/sourcecode/README.md
      .guild/sourcecode/guild.yml
      .guild/sourcecode/make_fs.py
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/
      l/d.txt
      l/e.txt
      l/f.bin
    <exit 0>

And to `--full-path` options.

    >>> guild_run("ls -Lf")
    ???/runs/aaaa/a
    .../runs/aaaa/b
    .../runs/aaaa/c
    .../runs/aaaa/c/d.txt
    .../runs/aaaa/c/e.txt
    .../runs/aaaa/c/f.bin
    .../runs/aaaa/l
    .../runs/aaaa/l/d.txt
    .../runs/aaaa/l/e.txt
    .../runs/aaaa/l/f.bin
    <exit 0>

List source code with `--sourcecode`.

    >>> guild_run("ls --sourcecode")
    ???/runs/aaaa/.guild/sourcecode:
      README.md
      guild.yml
      make_fs.py
    <exit 0>

Source code with full path.

    >>> guild_run("ls --sourcecode --full-path")
    ???/runs/aaaa/.guild/sourcecode/README.md
    .../runs/aaaa/.guild/sourcecode/guild.yml
    .../runs/aaaa/.guild/sourcecode/make_fs.py
    <exit 0>

Results can be filtered using a `--path` option.

    >>> guild_run("ls -p a")
    ???/runs/aaaa:
      a
    <exit 0>

    >>> guild_run("ls -p c --full-path")
    ???/runs/aaaa/c
    .../runs/aaaa/c/d.txt
    .../runs/aaaa/c/e.txt
    .../runs/aaaa/c/f.bin
    <exit 0>

    >>> guild_run("ls -p no-match")
    ???/runs/aaaa:
    <exit 0>

Paths can use wildcard patterns.

    >>> guild_run("ls -p '*/*.txt'")
    ???/runs/aaaa:
      c/d.txt
      c/e.txt
    <exit 0>

Patterns apply through to following links.

    >>> guild_run("ls -p '*/*.bin' -L")
    ???/runs/aaaa:
      c/f.bin
      l/f.bin
    <exit 0>

Paths are applied to the source code location.

    >>> guild_run("ls --sourcecode -p README.md")
    ???/runs/aaaa/.guild/sourcecode:
      README.md
    <exit 0>

    >>> guild_run("ls --sourcecode -p README.md -f")
    ???/runs/aaaa/.guild/sourcecode/README.md
    <exit 0>

## Alt Source Code Dest

The `alt-sourcecode` operation installs source code in the run
directory root rather than under `.guild/sourcecode`.

    >>> project.run("alt-sourcecode", run_id="bbbb")

The `ls` command knows to look there for source code.

    >>> guild_run("ls --sourcecode")
    ???/runs/bbbb:
      README.md
      guild.yml
      make_fs.py
    <exit 0>

The source code shows up in normal listings as it's no longer under
the private `.guild` directory.

    >>> guild_run("ls")
    ???/runs/bbbb:
      README.md
      guild.yml
      make_fs.py
    <exit 0>

`alt-sourcecode-2` installs source code in a `src` subdirectory.

    >>> project.run("alt-sourcecode-2", run_id="cccc")

    >>> guild_run("ls --sourcecode")
    ???/runs/cccc/src:
      README.md
      guild.yml
      make_fs.py
    <exit 0>

    >>> guild_run("ls")
    ???/runs/cccc:
      src/
      src/README.md
      src/guild.yml
      src/make_fs.py
    <exit 0>
