# Project source code

This is largely a duplication of similar builtin tests
`copysourcecode-*`. It's left in the event it provides added test
coverage. Tests here that are missing in the builtin tests should be
moved there and this file removed.

We need to create a copy of the `sourcecode` example to a directory
not managed by Git.

    >>> project = mkdtemp()
    >>> copytree(example("sourcecode"), project)
    >>> use_project(project)

## `default`

Test source code.

    >>> run("guild run default --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
    Selected for copy:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    Skipped:
      logo.png

Run op.

    >>> run("guild run default -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml
    subproject/__init__.py
    subproject/d.py
    subproject/e.csv
    subproject/guild.yml

## `include-png`

Test source code.

    >>> run("guild run include-png --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      include *.png
    Selected for copy:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      logo.png
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    Skipped:

Run op.

    >>> run("guild run include-png -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml
    logo.png
    subproject/__init__.py
    subproject/d.py
    subproject/e.csv
    subproject/guild.yml

## `exclude-paths`

Test source code.

    >>> run("guild run exclude-paths --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      exclude README.md
      exclude *.csv
    Selected for copy:
      a.py
      b.py
      c.py
      guild.yml
      subproject/__init__.py
      subproject/d.py
      subproject/guild.yml
    Skipped:
      README.md
      d.csv
      logo.png
      subproject/e.csv

Run op.

    >>> run("guild run exclude-paths -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    a.py
    b.py
    c.py
    guild.yml
    subproject/__init__.py
    subproject/d.py
    subproject/guild.yml

## `disable-sourcecode`

Test source code.

    >>> run("guild run disable-sourcecode --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude *
    Source code copy disabled

Run op.

    >>> run("guild run disable-sourcecode -y")
    guild: No module named a
    <exit 1>

Verify source code files.

    >>> run("guild ls --sourcecode")
    ???:
    <exit 0>

## `all-sourcecode`

Test source code.

    >>> run("guild run all-sourcecode --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      include *
    Selected for copy:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      logo.png
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    Skipped:

Run op.

    >>> run("guild run all-sourcecode -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml
    logo.png
    subproject/__init__.py
    subproject/d.py
    subproject/e.csv
    subproject/guild.yml

## `select-patterns`

Test source code.

    >>> run("guild run select-patterns --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      exclude *
      include guild.yml
      include *.py
    Selected for copy:
      a.py
      b.py
      c.py
      guild.yml
      subproject/__init__.py
      subproject/d.py
      subproject/guild.yml
    Skipped:
      README.md
      d.csv
      logo.png
      subproject/e.csv

Run op.

    >>> run("guild run select-patterns --yes")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    a.py
    b.py
    c.py
    guild.yml
    subproject/__init__.py
    subproject/d.py
    subproject/guild.yml

The alternative version selects only the root guild.yml.

    >>> run("guild run select-patterns-2 --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      exclude *
      include /guild.yml
      include *.py
    Selected for copy:
      a.py
      b.py
      c.py
      guild.yml
      subproject/__init__.py
      subproject/d.py
    Skipped:
      README.md
      d.csv
      logo.png
      subproject/e.csv
      subproject/guild.yml

## `copy-to-alt-dir`

Test source code.

    >>> run("guild run copy-to-alt-dir --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
    Selected for copy:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    Skipped:
      logo.png

Run op.

    >>> run("guild run copy-to-alt-dir -y")
    d
    c
    b
    a
    <exit 0>

Because `copy-to-alt-dir` specifies `src` as the alternative source
code dest, Guild lists this location when we use `--sourcecode` with
`ls`.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    src/README.md
    src/a.py
    src/b.py
    src/c.py
    src/d.csv
    src/guild.yml
    src/subproject/__init__.py
    src/subproject/d.py
    src/subproject/e.csv
    src/subproject/guild.yml

This is the same list of files as the default, but under `src`.

    >>> run("guild ls -n", ignore="pyc")  # doctest: +REPORT_UDIFF
    src/
    src/README.md
    src/a.py
    src/b.py
    src/c.py
    src/d.csv
    src/guild.yml
    src/subproject/
    src/subproject/__init__.py
    src/subproject/d.py
    src/subproject/e.csv
    src/subproject/guild.yml

## `copy-all-to-run-dir`

Test source code.

    >>> run("guild run copy-all-to-run-dir --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      exclude *
      include *
    Selected for copy:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      logo.png
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    Skipped:

Run op.

    >>> run("guild run copy-all-to-run-dir -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml
    logo.png
    subproject/__init__.py
    subproject/d.py
    subproject/e.csv
    subproject/guild.yml

## `exclude-dir`

Test source code.

    >>> run("guild run exclude-dir --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
      exclude dir subproject
    Selected for copy:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
    Skipped:
      subproject/
      logo.png

Run op.

    >>> run("guild run exclude-dir -y")
    Traceback (most recent call last):
    ...No module named ...subproject...
    <exit 1>

Verify source code.

    >>> run("guild ls -n --sourcecode", ignore="pyc")
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml

## Specifying alternative roots for sourcecode

    >>> cd(example("sourcecode/subproject"))

### `parent-root`

Test source code.

    >>> run("guild run parent-root --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from '..'
    Rules:
      exclude dir .guild
      exclude dir * containing .guild-nocopy
      exclude dir .git
      gitignore + guildignore patterns
      exclude .git*, .guildignore
    Selected for copy:
      ../README.md
      ../a.py
      ../b.py
      ../c.py
      ../d.csv
      ../guild.yml
      ../logo.png
      __init__.py
      d.py
      e.csv
      guild.yml
    Skipped:

Run op.

    >>> run("guild run parent-root -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")  # doctest: +REPORT_UDIFF
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml
    logo.png
    subproject/__init__.py
    subproject/d.py
    subproject/e.csv
    subproject/guild.yml

### `parent-root-excludes-subproject`

Test source code.

    >>> run("guild run parent-root-exclude-subproject --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from '..'
    Rules:
      exclude dir .guild
      exclude dir * containing .guild-nocopy
      exclude dir .git
      gitignore + guildignore patterns
      exclude .git*, .guildignore
      exclude subproject/*
    Selected for copy:
      ../README.md
      ../a.py
      ../b.py
      ../c.py
      ../d.csv
      ../guild.yml
      ../logo.png
    Skipped:
      __init__.py
      d.py
      e.csv
      guild.yml

Run the op.

    >>> run("guild run parent-root-exclude-subproject -y")
    Traceback (most recent call last):
    ...No module named ...subproject...
    <exit 1>

Verify source code files.

    >>> run("guild ls -n --sourcecode", ignore="pyc")
    README.md
    a.py
    b.py
    c.py
    d.csv
    guild.yml
    logo.png
