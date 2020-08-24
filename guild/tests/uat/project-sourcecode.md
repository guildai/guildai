# Project source code

    >>> cd(example("sourcecode"))

    >>> quiet("guild runs rm -y")

## `default`

Test source code:

    >>> run("guild run default --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
    Selected for copy:
      ./README.md
      ./a.py
      ./b.py
      ./c.py
      ./d.csv
      ./guild.yml
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/e.csv
      ./subproject/guild.yml
    Skipped:
      ./logo.png
    <exit 0>

Run op:

    >>> run("guild run default -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    <exit 0>

## `include-png`

Test source code:

    >>> run("guild run include-png --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      include '*.png'
    Selected for copy:
      ./README.md
      ./a.py
      ./b.py
      ./c.py
      ./d.csv
      ./guild.yml
      ./logo.png
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/e.csv
      ./subproject/guild.yml
    Skipped:
    <exit 0>

Run op:

    >>> run("guild run include-png -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      logo.png
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    <exit 0>

## `exclude-paths`

Test source code:

    >>> run("guild run exclude-paths --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      exclude 'README.md'
      exclude '*.csv'
    Selected for copy:
      ./a.py
      ./b.py
      ./c.py
      ./guild.yml
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/guild.yml
    Skipped:
      ./README.md
      ./d.csv
      ./logo.png
      ./subproject/e.csv
    <exit 0>

Run op:

    >>> run("guild run exclude-paths -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      a.py
      b.py
      c.py
      guild.yml
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/guild.yml
    <exit 0>

## `disable-sourcecode`

Test source code:

    >>> run("guild run disable-sourcecode --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude '*'
    Source code copy disabled
    <exit 0>

Run op:

    >>> run("guild run disable-sourcecode -y")
    guild: No module named a
    <exit 1>

Verify source code files:

    >>> run("guild ls --sourcecode")
    ???:
    <exit 0>

## `all-sourcecode`

Test source code:

    >>> run("guild run all-sourcecode --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      include '*'
    Selected for copy:
      ./README.md
      ./a.py
      ./b.py
      ./c.py
      ./d.csv
      ./guild.yml
      ./logo.png
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/e.csv
      ./subproject/guild.yml
    Skipped:
    <exit 0>

Run op:

    >>> run("guild run all-sourcecode -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      logo.png
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    <exit 0>

## `select-patterns`

Test source code:

    >>> run("guild run select-patterns --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      exclude '*'
      include 'guild.yml'
      include '*.py'
    Selected for copy:
      ./a.py
      ./b.py
      ./c.py
      ./guild.yml
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/guild.yml
    Skipped:
      ./README.md
      ./d.csv
      ./logo.png
      ./subproject/e.csv
    <exit 0>

Run op:

    >>> run("guild run select-patterns --yes")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      a.py
      b.py
      c.py
      guild.yml
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/guild.yml
    <exit 0>

The alternative version selects only the root guild.yml:

    >>> run("guild run select-patterns-2 --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      exclude '*'
      include '/guild.yml'
      include '*.py'
    Selected for copy:
      ./a.py
      ./b.py
      ./c.py
      ./guild.yml
      ./subproject/__init__.py
      ./subproject/d.py
    Skipped:
      ./README.md
      ./d.csv
      ./logo.png
      ./subproject/e.csv
      ./subproject/guild.yml
    <exit 0>

## `copy-to-alt-dir`

Test source code:

    >>> run("guild run copy-to-alt-dir --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
    Selected for copy:
      ./README.md
      ./a.py
      ./b.py
      ./c.py
      ./d.csv
      ./guild.yml
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/e.csv
      ./subproject/guild.yml
    Skipped:
      ./logo.png
    <exit 0>

Run op:

    >>> run("guild run copy-to-alt-dir -y")
    d
    c
    b
    a
    <exit 0>

Nothing is copied to the source code location:

    >>> run("guild ls --sourcecode")
    ???:
    <exit 0>

Instead, source code files are normal run files copied to alt dest:

    >>> run("guild ls", ignore="pyc")
    ???:
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
    <exit 0>

## `copy-all-to-run-dir`

Test source code:

    >>> run("guild run copy-all-to-run-dir --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      exclude '*'
      include '*'
    Selected for copy:
      ./README.md
      ./a.py
      ./b.py
      ./c.py
      ./d.csv
      ./guild.yml
      ./logo.png
      ./subproject/__init__.py
      ./subproject/d.py
      ./subproject/e.csv
      ./subproject/guild.yml
    Skipped:
    <exit 0>

Run op:

    >>> run("guild run copy-all-to-run-dir -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode")
    ???:
    <exit 0>

    >>> run("guild ls", ignore="pyc")
    ???:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      logo.png
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    <exit 0>

## `exclude-dir`

Test source code:

    >>> run("guild run exclude-dir --test-sourcecode")
    Copying from the current directory
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      exclude dir 'subproject'
    Selected for copy:
      ./README.md
      ./a.py
      ./b.py
      ./c.py
      ./d.csv
      ./guild.yml
    Skipped:
      ./subproject
      ./logo.png
    <exit 0>

Run op:

    >>> run("guild run exclude-dir -y")
    Traceback (most recent call last):
    ...No module named ...subproject...
    <exit 1>

Verify source code:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
    <exit 0>

## Specifying alternative roots for sourcecode

    >>> cd(example("sourcecode/subproject"))

### `parent-root`

Test source code:

    >>> run("guild run parent-root --test-sourcecode")
    Copying from '..'
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
    Selected for copy:
      ../README.md
      ../a.py
      ../b.py
      ../c.py
      ../d.csv
      ../guild.yml
      ../subproject/__init__.py
      ../subproject/d.py
      ../subproject/e.csv
      ../subproject/guild.yml
    Skipped:
      ../logo.png
    <exit 0>

Run op:

    >>> run("guild run parent-root -y")
    d
    c
    b
    a
    <exit 0>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
      subproject/
      subproject/__init__.py
      subproject/d.py
      subproject/e.csv
      subproject/guild.yml
    <exit 0>

### `parent-root-excludes-subproject`

Test source code:

    >>> run("guild run parent-root-exclude-subproject --test-sourcecode")
    Copying from '..'
    Rules:
      exclude dir '__pycache__'
      exclude dir '.*'
      exclude dir '*' with '.guild-nocopy'
      exclude dir '*' with 'bin/activate'
      exclude dir 'build'
      exclude dir '*.egg-info'
      include text '*' size < 1048577, max match 100
      exclude 'subproject/*'
    Selected for copy:
      ../README.md
      ../a.py
      ../b.py
      ../c.py
      ../d.csv
      ../guild.yml
    Skipped:
      ../logo.png
      ../subproject/__init__.py
      ../subproject/d.py
      ../subproject/e.csv
      ../subproject/guild.yml
    <exit 0>

Run op:

    >>> run("guild run parent-root-exclude-subproject -y")
    Traceback (most recent call last):
    ...No module named ...subproject...
    <exit 1>

Verify source code files:

    >>> run("guild ls --sourcecode", ignore="pyc")
    ???/.guild/sourcecode:
      README.md
      a.py
      b.py
      c.py
      d.csv
      guild.yml
    <exit 0>
