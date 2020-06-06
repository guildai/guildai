# Guild Example: `project-sourcecode`

This example illustrates how the `sourcecode` attribute is used to
configure how project source code is copied for an operation.

- [guild.yml](guild.yml) - Project Guild file
- `*.py` files - Sample Python source code files
- `*.png` files - Sample images used to represent binary (non-text)
  files
- `*.csv` - Sample CSV fiels
- [subproject](subproject) - Sample subproject used to illustrate
  alternative project source code roots

## Background

When Guild runs an operation, it creates a new, empty directory that
serves as the *run directory*. The run process is started using this
directory as the working directory. *Relative paths are therefore
relative to to the run directory, not the project directory.*

Additionally, for Python based operations, Guild configures the Python
system path &mdash; the path used to resolve Python package and module
locations) &mdash; to use the run directory and not the project
directory. This ensures that a run directory must contain all of the
source code needed to run the operation, apart from Python modules
installed in the environment.

To make source code available, Guild copies files from the project
directory to the run directory under the `.guild/sourcecode`
subdirectory. You can list source code files for a run using the
command;

```
$ guild ls --sourcecode
```

Guild automatically includes `.guild/sourcecode` in the Python system
path when running a Python based operation. Guild does not
automatically include this location in paths for other language
environments &mdash; this must be configured using command arguments
in `exec` or by defining the applicable environment variable.

The result of this example describes various configurations used to
copy source code for a run. The examples are specific to Python
programs, but can be generalized to other languages.

All of the examples can be tested by running operations with the
`--test-sourcecode` option. When this option is used, Guild does not
run the operation but instead shows which files would be copied and
which files would be skipped given the rules defined under the
`sourcecode` attribute.

## Default source code copy

By default, Guild applies the following rules when copying source
code:

- Source code must be a text file
- Source code must be smaller than 1M
- Guild stops copying source code files after 100 files

Under the default rules, if Guild finds large files or too many files,
it prints a warning message.

You change the default behavior by defining `sourcecode` attributes
for an operation. You can also define `sourcecode` for a model, which
applies to the model's operations by default.

Use the `default` operation to see which files Guild copies as source
code by default.

``` yaml
default:
  description: No sourcecode configuration - shows default copy behavior
  main: a
```

Show which files are considered source code:

```
$ guild run default --test-sourcecode
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
  ./subproject/d.py
  ./subproject/e.csv
  ./subproject/guild.yml
Skipped:
  ./logo.png
```

Guild shows the copy rules, the files selected, and the files skipped.

Note that Guild skips `logo.png` because it's doesn't match any of the
include rules &mdash; i.e. it's not a text file.

## Include additional files

To extend the default source code rules, add additional include or
exclude patterns.

For example, the `include-png` operation includes `*.png` files.

``` yaml
include-png:
  description: Extend default behavior to include png files
  main: a
  sourcecode:
    - include: '*.png'
```

Confirm that `logo.png` is included in the list selected files:

```
$ guild run include-png --test-sourcecode
```

If you want to run the operation to confirm that `logo.png` is in fact
copied, run the following:

```
$ guild run include-png -y
$ guild ls --sourcecode
```

## Exclude files

To exclude a file that would otherwise be selected from previously
defined rules, use one or more `exclude` patterns.

The `exclude-paths` operation excludes `README.md`.

``` yaml
exclude-paths:
  description: Extend default behavior to exclude README.md and CSV files
  main: a
  sourcecode:
    - exclude: README.md
    - exclude: '*.csv'
```

## Disable source code copies

If your operation does not need files copied as source code, you can
disable source code altogether by setting `sourcecode` to `no` or to
an empty list.

The `disable-sourcecode` operation prevents any files from being
copied as source code.

``` yaml
disable-sourcecode:
  description: Disable source code copies
  main: a
  sourcecode: no
```

## Copy all files

Use `include: '*'` to include all project files as source code.

``` yaml
all-sourcecode:
  description: Include all files as source code
  main: a
  sourcecode:
    - include: '*'
```

## Copy only files matching specific patterns

To copy only files matching a list of string patterns, list those
patterns directly (i.e. without specifying `include`) under
`sourcecode`.

The `select-patterns` operation uses this pattern.

``` yaml
select-patterns:
  description: Only copy files matching specified patterns
  main: a
  sourcecode:
    - guild.yml
    - '*.py'
```

## Copy source files to an alternative location

By default Guild copies source code files to `.guild/sourcecode`. The
rationale for this is that the run directory reflects the artifacts
used and generated by an operation. Source code, while an important
artifact that must be included in each experiment, is not the primary
artifact of concern. Guild therefore saves source code as a part of
the run metadata.

If you prefer to copy source code to a different location under the
run directory, use the `dest` attribute of `sourcecode`.

Two operation illustrate this: `copy-to-alt-dir` and
`copy-all-to-run-dir`.

`copy-to-alt-dir` copies selected source code files to the `src`
subdirectory.

``` yaml
copy-to-alt-dir:
  description: Copy source code files to src under run directory
  main: a
  sourcecode:
    dest: src
```

`copy-all-to-run-dir` copies the entire project to the run directory.

``` yaml
copy-all-to-run-dir:
  description: Copy all projects to the run directory
  main: a
  sourcecode:
    dest: .
    select: '*'
```

If source code files are copied to an alternative location using
`dest`, Guild will not consider those files to be source code for
commands like `guild ls`. E.g. `guild ls --sourcecode` will show an
empty list for both of the options above. The source code files are
visible as normal run files.

## Exclude directories from scanning

By default, Guild scans all files under the project directory for
consideration as source code files. In cases where a directory
contains a large number of non-source files, you can exclude this
directory from scanning by specifying it explicitly as a directory.

The `exclude-dir` operation illustrates this.

``` yaml
exclude-dir:
  description: Exclude a directory explicitly for optimized copies
  main: a
  sourcecode:
    - exclude:
        dir: subproject
```

## Alternative source code root

By default, Guild copies source code from the directory containing the
Guild file. You can specify an alternative source using the `root`
attribute of `sourcecode`.

The [`subproject`](subproject) directory contains a Guild file that
defines two operations that both specify an alternative root.

`parent-root` uses `..` to indicate that the subproject parent
directory is used as the source code root.

``` yaml
parent-root:
  main: a
  sourcecode:
    root: ..
```

Use the `select` attribute with `root` to control the source code
select rules.

`parent-root-exclude-subproject` illustrates:

``` yaml
parent-root-exclude-subproject:
  main: a
  sourcecode:
    root: ..
    select:
      - exclude: subproject
```
