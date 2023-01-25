# Publishing Runs

The `runs publish` commands is used to publish runs. A published run
is the public interface to a run. It consists of:

- Run info as formatted files
- Template generated report
- Run files
- Run source code

We use the `publish` sample project.

    >>> cd(sample("projects/publish"))

    >>> guild_home = mkdtemp()
    >>> set_guild_home(guild_home)

Generate a run for each of the four operations defined in the project.

    >>> run("guild run op --run-id=aaa -y")
    x: 3
    y: 1
    <exit 0>

    >>> run("guild run op2 --run-id=bbb -y")
    <exit 0>

    >>> run("guild run op3 --run-id=ccc -y")
    Resolving file:src.txt
    x: 3
    y: 1
    z: 2
    <exit 0>

    >>> run("guild run legacy-sourcecode --run-id=ddd -y")
    Resolving file:just-files/README.md
    x: 3
    y: 1
    <exit 0>

    >>> run("guild runs")
    [1:ddd]  legacy-sourcecode  ...  completed
    [2:ccc]  op3                ...  completed  c=4
    [3:bbb]  op2                ...  completed
    [4:aaa]  op                 ...  completed  a=1 b=2
    <exit 0>

## Published files

When publishing a run, Guild copies source code and optionally a set
of run files. The set of run files is determined by the command
options and the operation definition.

Unless specified using the `--files` or `--all-files` flag to the
command, Guild only copies source code files.

### Source code files

By default, Guild only copies source code files for a published
run. See below for examples using `--files` and `--all-files` where
Guild also copies non-sourcecode run files.

Publish the runs using default options.

    >>> publish_dest = mkdtemp()

    >>> run(f"guild publish --dest={publish_dest} -y")
    Publishing [ddd] legacy-sourcecode... using ...
    Publishing [ccc] op3... using ...
    Publishing [bbb] op2... using ...
    Publishing [aaa] op... using ...
    Refreshing runs index
    Published runs using ...

For each run Guild generates run metadata and applies the default
template. It copies source code for each run to a `sourcecode`
subdirectory.

    >>> find(publish_dest)  # doctest: +REPORT_UDIFF
    .guild-nocopy
    README.md
    aaa/README.md
    aaa/flags.yml
    aaa/output.txt
    aaa/run.yml
    aaa/runfiles.csv
    aaa/scalars.csv
    aaa/sourcecode.csv
    aaa/sourcecode/op.py
    bbb/README.md
    bbb/flags.yml
    bbb/output.txt
    bbb/run.yml
    bbb/runfiles.csv
    bbb/scalars.csv
    bbb/some_other_file.md
    bbb/sourcecode.csv
    ccc/README.md
    ccc/flags.yml
    ccc/output.txt
    ccc/run.yml
    ccc/runfiles.csv
    ccc/scalars.csv
    ccc/sourcecode.csv
    ccc/sourcecode/op3.py
    ccc/sourcecode/op.py
    ddd/README.md
    ddd/flags.yml
    ddd/output.txt
    ddd/run.yml
    ddd/runfiles.csv
    ddd/scalars.csv
    ddd/sourcecode.csv
    ddd/sourcecode/op3.py
    ddd/sourcecode/op.py
    ddd/sourcecode/src.txt

Confirm that each run source code copy matches the source code listing
from the `ls` command.

The operation `op` (run 'aaa') specifies a single source code file
`op.py`.

    >>> find(path(publish_dest, "aaa", "sourcecode"))
    op.py

    >>> run("guild ls -ns aaa")
    op.py
    <exit 0>

The operation `op2` (run 'bbb') disables source code copies and so
these lists are empty.

    >>> find(path(publish_dest, "bbb", "sourcecode"))
    <empty>

    >>> run("guild ls -ns bbb")
    <exit 0>

Operation `op3` (run 'ccc') selects `*.py` files for source code.

    >>> find(path(publish_dest, "ccc", "sourcecode"))
    op3.py
    op.py

    >>> run("guild ls -ns ccc")
    op3.py
    op.py
    <exit 0>

Operation `legacy-sourcecode` (run 'ddd') copies source code files to
the legacy location `.guild/sourcecode`. The source code files are
copied directly to the published run under the `sourcecode`
subdirectory.

    >>> find(path(publish_dest, "ddd", "sourcecode"))
    op3.py
    op.py
    src.txt

    >>> run("guild ls -ns ddd")
    .guild/sourcecode/op3.py
    .guild/sourcecode/op.py
    .guild/sourcecode/src.txt
    <exit 0>

### Default run files

The `--files` option tells Guild to copy any operation-defined publish
files for a run. Such files are selected using the `publish.files`
operation attribute.

    >>> publish_dest = mkdtemp()

    >>> quiet(f"guild publish --files --dest={publish_dest} -y")

The published runs now include run files, which are copied under the
`runfiles` subdirectory for each run.

    >>> find(publish_dest)  # doctest: +REPORT_UDIFF
    .guild-nocopy
    README.md
    aaa/README.md
    aaa/flags.yml
    aaa/output.txt
    aaa/run.yml
    aaa/runfiles.csv
    aaa/runfiles/generated-1.txt
    aaa/runfiles/generated-2.txt
    aaa/scalars.csv
    aaa/sourcecode.csv
    aaa/sourcecode/op.py
    bbb/README.md
    bbb/flags.yml
    bbb/output.txt
    bbb/run.yml
    bbb/runfiles.csv
    bbb/scalars.csv
    bbb/some_other_file.md
    bbb/sourcecode.csv
    ccc/README.md
    ccc/flags.yml
    ccc/output.txt
    ccc/run.yml
    ccc/runfiles.csv
    ccc/runfiles/generated-1.txt
    ccc/runfiles/generated-3.txt
    ccc/scalars.csv
    ccc/sourcecode.csv
    ccc/sourcecode/op3.py
    ccc/sourcecode/op.py
    ddd/README.md
    ddd/flags.yml
    ddd/output.txt
    ddd/run.yml
    ddd/runfiles.csv
    ddd/runfiles/dep.md
    ddd/runfiles/generated-1.txt
    ddd/scalars.csv
    ddd/sourcecode.csv
    ddd/sourcecode/op3.py
    ddd/sourcecode/op.py
    ddd/sourcecode/src.txt

In this case, the selected run files are determined by the operation
`publish` configuration.

### All run files

The `--all-files` option tells Guild to copy all run files with the
excetion of links. Links can be copied using `--include-links` (see below).

    >>> publish_dest = mkdtemp()

`--all-files` cannot be used with `--files` as they are mutually
exclusive options.

    >>> run(f"guild publish --all-files --files --dest={publish_dest} -y")
    guild: --files and --all-files cannot both be used
    <exit 1>

Publish runs with `--all-files`:

    >>> quiet(f"guild publish --all-files --dest={publish_dest} -y")

Copies files now include all of the non-source code run files under
`runfiles`, with the exception of links.

    >>> find(publish_dest)  # doctest: +REPORT_UDIFF
    .guild-nocopy
    README.md
    aaa/README.md
    aaa/flags.yml
    aaa/output.txt
    aaa/run.yml
    aaa/runfiles.csv
    aaa/runfiles/generated-1.txt
    aaa/runfiles/generated-2.txt
    aaa/scalars.csv
    aaa/sourcecode.csv
    aaa/sourcecode/op.py
    bbb/README.md
    bbb/flags.yml
    bbb/output.txt
    bbb/run.yml
    bbb/runfiles.csv
    bbb/scalars.csv
    bbb/some_other_file.md
    bbb/sourcecode.csv
    ccc/README.md
    ccc/flags.yml
    ccc/output.txt
    ccc/run.yml
    ccc/runfiles.csv
    ccc/runfiles/generated-1.txt
    ccc/runfiles/generated-2.txt
    ccc/runfiles/generated-3.txt
    ccc/scalars.csv
    ccc/sourcecode.csv
    ccc/sourcecode/op3.py
    ccc/sourcecode/op.py
    ddd/README.md
    ddd/flags.yml
    ddd/output.txt
    ddd/run.yml
    ddd/runfiles.csv
    ddd/runfiles/dep.md
    ddd/runfiles/generated-1.txt
    ddd/runfiles/generated-2.txt
    ddd/scalars.csv
    ddd/sourcecode.csv
    ddd/sourcecode/op3.py
    ddd/sourcecode/op.py
    ddd/sourcecode/src.txt

We can verify that the copied run files correspond to the non-source
code files for each run. We use the short form of the `--generated`and
`--dependencies` options.

Op `op` (run 'aaa') generates two files and has no dependencies.

    >>> find(path(publish_dest, "aaa", "runfiles"))
    generated-1.txt
    generated-2.txt

    >>> run("guild ls -ndg aaa")
    generated-1.txt
    generated-2.txt
    <exit 0>

Op `op2` (run 'bbb') does not generate any files and doesn't have any
dependencies.

    >>> find(path(publish_dest, "bbb", "runfiles"))
    <empty>

    >>> run("guild ls -ndg bbb")
    <exit 0>

Op `op3` (run 'ccc') generates three files and includes a symlinked
dependency. By default Guild does not copy links.

    >>> find(path(publish_dest, "ccc", "runfiles"))
    generated-1.txt
    generated-2.txt
    generated-3.txt

We see the linked file in the listing with `ls`.

    >>> run("guild ls -ndg ccc")
    generated-1.txt
    generated-2.txt
    generated-3.txt
    link.txt
    <exit 0>

Op `legacy-sourcecode` generates two files and includes a copied file
dependency. This file is copied for the publish.

    >>> find(path(publish_dest, "ddd", "runfiles"))
    dep.md
    generated-1.txt
    generated-2.txt

    >>> run("guild ls -ndg ddd")
    dep.md
    generated-1.txt
    generated-2.txt
    <exit 0>

### Including links

The `--include-links` option tells Guild to copy run file links when
publishing a run.

Let's publish the run for operation `op3` (run 'ccc'), which uses a
linked file as a dependency.

    >>> publish_dest = mkdtemp()

    >>> quiet(f"guild publish ccc --all-files --include-links --dest={publish_dest} -y")

    >>> find(publish_dest)
    ???
    ccc/runfiles/link.txt
    ...

## Run metadata

Guild generates several run metadata files for each published
run. These files can be referenced by templates or otherwise used to
show information about a run.

Let's look at the files generated by the latest publish command (for
run 'ccc').

    >>> find(publish_dest)
    .guild-nocopy
    README.md
    ccc/README.md
    ccc/flags.yml
    ccc/output.txt
    ccc/run.yml
    ccc/runfiles.csv
    ccc/runfiles/generated-1.txt
    ccc/runfiles/generated-2.txt
    ccc/runfiles/generated-3.txt
    ccc/runfiles/link.txt
    ccc/scalars.csv
    ccc/sourcecode.csv
    ccc/sourcecode/op3.py
    ccc/sourcecode/op.py

### Index README.md

Published runs are included in a top-level `README.md` index. This
index is generated by the default template and can be customized by
the user. See below for custom templates.

    >>> cat(path(publish_dest, "README.md"))
    # Published runs
    <BLANKLINE>
    | ID | Operation | Started | Time | Status | Label |
    | -- | --------- | ------- | ---- | ------ | ----- |
    | [ccc](ccc/README.md) | op3 | ... UTC | 0:00:... | completed | c=4 |
    <BLANKLINE>

### Run README.md

The `README.md` file within each published run directory is generated
by the template. In this case the default template is used. See below
for custom templates.

    >>> cat(path(publish_dest, "ccc", "README.md"))  # doctest: +REPORT_UDIFF
    [Published runs](../README.md)
    <BLANKLINE>
    # op3
    <BLANKLINE>
    | ID                   | Operation           | Started                  | Time                | Status           | Label                |
    | --                   | ---------           | ---------                | ----                | ------           | -----                |
    | ccc | op3 | ... UTC | 0:00:00 | completed | c=4 |
    <BLANKLINE>
    [run.yml](run.yml)
    <BLANKLINE>
    ## Contents
    <BLANKLINE>
    - [Flags](#flags)
    - [Scalars](#scalars)
    - [Run Files](#run-files)
    - [Source Code](#source-code)
    - [Output](#output)
    <BLANKLINE>
    ## Flags
    <BLANKLINE>
    | Name | Value |
    | ---- | ----- |
    | c | 4 |
    <BLANKLINE>
    [flags.yml](flags.yml)
    <BLANKLINE>
    ## Scalars
    <BLANKLINE>
    | Key | Step | Value |
    | --- | ---- | ----- |
    | x | 0 | 3.0 |
    | y | 0 | 1.0 |
    | z | 0 | 2.0 |
    <BLANKLINE>
    [scalars.csv](scalars.csv)
    <BLANKLINE>
    ## Run Files
    <BLANKLINE>
    | Path | Type | Size | Modified | MD5 |
    | ---- | ---- | ---- | -------- | --- |
    | [generated-1.txt](runfiles/generated-1.txt) | file | 5 | ... UTC | 8c8432c5523c8507a5ec3b1ae3ab364f |
    | [generated-2.txt](runfiles/generated-2.txt) | file | 9 | ... UTC | 7cbef5232b2e916eccc41d756d05035f |
    | [generated-3.txt](runfiles/generated-3.txt) | file | 7 | ... UTC | 4f6eabeaa60af0c1e30869b32242c615 |
    | [link.txt](runfiles/link.txt) | file link | 6 | ... UTC | 09f7e02f1290be211da707a266f153b3 |
    <BLANKLINE>
    [runfiles.csv](runfiles.csv)
    <BLANKLINE>
    ## Source Code
    <BLANKLINE>
    | Path | Size | Modified | MD5 |
    | ---- | ---- | -------- | --- |
    | [op3.py](sourcecode/op3.py) | 92 | ... UTC | 1bcc6bbc21e94b368ca2e3eea24c840c |
    | [op.py](sourcecode/op.py) | 154 | ... UTC | d7fa082a3b7eb573c27a248ee189528e |
    <BLANKLINE>
    [sourcecode.csv](sourcecode.csv)
    <BLANKLINE>
    ## Output
    <BLANKLINE>
    ```
    x: 3
    y: 1
    z: 2
    ```
    <BLANKLINE>
    [output.txt](output.txt)
    <BLANKLINE>

### Flags

The `flags.yml` file contains the flag values used for the run.

    >>> cat(path(publish_dest, "ccc", "flags.yml"))
    c: 4

### Output

`output.txt` contains the combined standard outout and standard error
for the run.

    >>> cat(path(publish_dest, "ccc", "output.txt"))
    x: 3
    y: 1
    z: 2

### Run info

`run.yml` contains general run information.

    >>> cat(path(publish_dest, "ccc", "run.yml"))
    id: ccc
    operation: op3
    status: completed
    started: ... UTC
    stopped: ... UTC
    time: 0:00:...
    marked: 'no'
    label: c=4
    command: ... -um guild.op_main op3 -- --c 4
    exit_status: 0

### Run files

`runfiles.csv` contains a list of all run files (non source code
files). This file is the complete listing of run files and not the
list of published run files.

    >>> cat(path(publish_dest, "ccc", "runfiles.csv"))
    path,type,size,mtime,md5
    generated-1.txt,file,5,...
    generated-2.txt,file,9,...
    generated-3.txt,file,7,...
    link.txt,file link,6,...

Each of the run files (from the run directory):

    >>> cat(path(guild_home, "runs", "ccc", "generated-1.txt"))
    Hola

    >>> cat(path(guild_home, "runs", "ccc", "generated-2.txt"))
    Yo yo yo

    >>> cat(path(guild_home, "runs", "ccc", "generated-3.txt"))
    Super!

    >>> cat(path(guild_home, "runs", "ccc", "link.txt"))
    Hello

Compare each run file to the copies in the published location.

    >>> def diff_ccc_runfile(filename):
    ...     diff(
    ...         path(guild_home, "runs", "ccc", filename),
    ...         path(publish_dest, "ccc", "runfiles", filename)
    ...     )

    >>> diff_ccc_runfile("generated-1.txt")

    >>> diff_ccc_runfile("generated-2.txt")

    >>> diff_ccc_runfile("generated-3.txt")

    >>> diff_ccc_runfile("link.txt")

### Scalars

`scalars.csv` is a list of scalars generated by the run.

    >>> cat(path(publish_dest, "ccc", "scalars.csv"))
    prefix,tag,count,total,avg_val,first_val,first_step,last_val,last_step,min_val,min_step,max_val,max_step
    .guild,x,1,3.0,3.0,3.0,0,3.0,0,3.0,0,3.0,0
    .guild,y,1,1.0,1.0,1.0,0,1.0,0,1.0,0,1.0,0
    .guild,z,1,2.0,2.0,2.0,0,2.0,0,2.0,0,2.0,0

### Source code files

`sourcecode.csv` is the list of source code files for the run.

    >>> cat(path(publish_dest, "ccc", "sourcecode.csv"))
    path,type,size,mtime,md5
    op3.py,file,92,...
    op.py,file,154,...

The source code files (from the run directory):

    >>> cat(path(guild_home, "runs", "ccc", "op3.py"))
    import op
    <BLANKLINE>
    c = 4
    <BLANKLINE>
    print(f"z: {c - op.b}")
    <BLANKLINE>
    open("generated-3.txt", "wb").write(b"Super!\n")

    >>> cat(path(guild_home, "runs", "ccc", "op3.py"))
    import op
    <BLANKLINE>
    c = 4
    <BLANKLINE>
    print(f"z: {c - op.b}")
    <BLANKLINE>
    open("generated-3.txt", "wb").write(b"Super!\n")

Compare each run source code file to the copies in the published
location.

    >>> def diff_ccc_sourcecode(filename):
    ...     diff(
    ...         path(guild_home, "runs", "ccc", filename),
    ...         path(publish_dest, "ccc", "sourcecode", filename)
    ...     )

    >>> diff_ccc_sourcecode("op.py")

    >>> diff_ccc_sourcecode("op3.py")

## Custom templates

Projects can define custom templates used in publishing. Guild uses
templates to generate reports for a published run. Guild supports a
flexible scheme that lets template authors selectively reuse and
override default template parts.

The tests below illustrate techniques that can be applied by custom
templates.

### Extending default and redefining blocks (template `t1`)

Template `t1` extends `publish-default/README.md` and redefines each
block in the default template.

    >>> publish_dest = mkdtemp()

    >>> quiet(f"guild publish ccc --template=t1 --dest={publish_dest} -y")

The generated template:

    >>> cat(path(publish_dest, "ccc", "README.md"))  # doctest: +REPORT_UDIFF
    [< Back to published runs](../README.md)
    <BLANKLINE>
    # Guild Run ccc
    <BLANKLINE>
    *op3 c=4*
    <BLANKLINE>
    | Attribute | Value               |
    |-----------|---------------------|
    | ID        | ccc        |
    | Operation | op3 |
    | Started   | ... UTC   |
    | Stopped   | ... UTC   |
    | Duration  | 0:00:...      |
    | Label     | c=4     |
    <BLANKLINE>
    ## Contents
    <BLANKLINE>
    - [Flags](#flags)
    - [Scalars](#scalars)
    - [Run Files](#run-files)
    - [Source Code](#source-code)
    - [Output](#output)
    <BLANKLINE>
    ## Flags
    <BLANKLINE>
    Flags are user-defined input to the run. The following flags were used
    for this run:
    <BLANKLINE>
    | Name | Value |
    |------|-------|
    | c | 4 |
    <BLANKLINE>
    ## Scalars
    <BLANKLINE>
    Scalars are metrics generated during a run.
    <BLANKLINE>
    | Key | Last Logged Value |
    |-----|-------------------|
    | x | 3.0 (step 0) |
    | y | 1.0 (step 0) |
    | z | 2.0 (step 0) |
    <BLANKLINE>
    ## Run Files
    <BLANKLINE>
    *Run files* are non-source code files. They're either inputs to the
    run (dependencies) or outputs (generated files).
    <BLANKLINE>
    The following files are associated with this run:
    <BLANKLINE>
     - generated-1.txt
     - generated-2.txt
     - generated-3.txt
     - link.txt
    <BLANKLINE>
    ## Source Code
    <BLANKLINE>
    | Path | Size | Modified | MD5 |
    | ---- | ---- | -------- | --- |
    | [op3.py](sourcecode/op3.py) | 92 | ... UTC | 1bcc6bbc21e94b368ca2e3eea24c840c |
    | [op.py](sourcecode/op.py) | 154 | ... UTC | d7fa082a3b7eb573c27a248ee189528e |
    <BLANKLINE>
    [sourcecode.csv](sourcecode.csv)
    <BLANKLINE>
    ## Output
    <BLANKLINE>
    The following output was generated for this run:
    <BLANKLINE>
    ```
    x: 3
    y: 1
    z: 2
    ```
    <BLANKLINE>
    ---
    <BLANKLINE>
    *This file was generated by a custom template*
    <BLANKLINE>

### New template with include (template `t2`)

Template `t2` replaces the default entirely but includes the default
flags template `published-default/_flags.md`.

    >>> quiet(f"guild publish aaa --dest {publish_dest} --template=t2 -y")

    >>> cat(path(publish_dest, "aaa", "README.md"))
    # Totally new report
    <BLANKLINE>
    Run: aaa
    <BLANKLINE>
    ## Flags (included)
    <BLANKLINE>
    | Name | Value |
    | ---- | ----- |
    | a | 1 |
    | b | 2 |
    <BLANKLINE>
    [flags.yml](flags.yml)
    <BLANKLINE>

### Extend default with block def and redefined include (template `t3`)

Template `t3` extends default and defines header and footer blocks. It
also redefines the `_flags.md` include.

    >>> quiet(f"guild publish ccc --dest={publish_dest} --template=t3 -y")

    >>> cat(path(publish_dest, "ccc", "README.md")) # doctest: +REPORT_UDIFF
    Ze header
    <BLANKLINE>
    # op3
    <BLANKLINE>
    | ID                   | Operation           | Started                  | Time                | Status           | Label                |
    | --                   | ---------           | ---------                | ----                | ------           | -----                |
    | ccc | op3 | ... UTC | 0:00:00 | completed | c=4 |
    <BLANKLINE>
    [run.yml](run.yml)
    <BLANKLINE>
    ## Contents
    <BLANKLINE>
    - [Flags](#flags)
    - [Scalars](#scalars)
    - [Run Files](#run-files)
    - [Source Code](#source-code)
    - [Output](#output)
    <BLANKLINE>
    ## Flags
    <BLANKLINE>
    Redef of flags
    ## Scalars
    <BLANKLINE>
    | Key | Step | Value |
    | --- | ---- | ----- |
    | x | 0 | 3.0 |
    | y | 0 | 1.0 |
    | z | 0 | 2.0 |
    <BLANKLINE>
    [scalars.csv](scalars.csv)
    ## Run Files
    <BLANKLINE>
    | Path | Type | Size | Modified | MD5 |
    | ---- | ---- | ---- | -------- | --- |
    | generated-1.txt | file | 5 | ... UTC | 8c8432c5523c8507a5ec3b1ae3ab364f |
    | generated-2.txt | file | 9 | ... UTC | 7cbef5232b2e916eccc41d756d05035f |
    | generated-3.txt | file | 7 | ... UTC | 4f6eabeaa60af0c1e30869b32242c615 |
    | link.txt | file link | 6 | ... UTC | 09f7e02f1290be211da707a266f153b3 |
    <BLANKLINE>
    [runfiles.csv](runfiles.csv)
    ## Source Code
    <BLANKLINE>
    | Path | Size | Modified | MD5 |
    | ---- | ---- | -------- | --- |
    | [op3.py](sourcecode/op3.py) | 92 | ... UTC | 1bcc6bbc21e94b368ca2e3eea24c840c |
    | [op.py](sourcecode/op.py) | 154 | ... UTC | d7fa082a3b7eb573c27a248ee189528e |
    <BLANKLINE>
    [sourcecode.csv](sourcecode.csv)
    ## Output
    <BLANKLINE>
    ```
    x: 3
    y: 1
    z: 2
    ```
    <BLANKLINE>
    [output.txt](output.txt)
    <BLANKLINE>
    Ze footer
    <BLANKLINE>

### Run files

Template `just-files` includes only the default run file template part
`publish-default/_runfiles.md`. We'll use this template to show how
run file lists are rendered by the default template.

Publish using a `just-files` template (only prints the files table):

    >>> quiet(f"guild publish ccc --dest={publish_dest} --template=just-files -y")

    >>> cat(path(publish_dest, "ccc", "README.md"))
    | Path | Type | Size | Modified | MD5 |
    | ---- | ---- | ---- | -------- | --- |
    | generated-1.txt | file | 5 | ... UTC | 8c8432c5523c8507a5ec3b1ae3ab364f |
    | generated-2.txt | file | 9 | ... UTC | 7cbef5232b2e916eccc41d756d05035f |
    | generated-3.txt | file | 7 | ... UTC | 4f6eabeaa60af0c1e30869b32242c615 |
    | link.txt | file link | 6 | ... UTC | 09f7e02f1290be211da707a266f153b3 |
    <BLANKLINE>
    [runfiles.csv](runfiles.csv)
    <BLANKLINE>

Note that the file type for `link.txt` is a file link. Note also that
neither of the run files contain hyperlinks to their sources because
the published run doesn't contain either run file.

When we publish with the `--all-files` option, the published run has
access to the run files.

    >>> quiet(
    ...     f"guild publish ccc --dest={publish_dest} --template=just-files "
    ...      "--all-files -y"
    ... )

In this case, the non-link files have hyperlinks in the table.

    >>> cat(path(publish_dest, "ccc", "README.md"))
    | Path | Type | Size | Modified | MD5 |
    | ---- | ---- | ---- | -------- | --- |
    | [generated-1.txt](runfiles/generated-1.txt) | file | 5 | ... UTC | 8c8432c5523c8507a5ec3b1ae3ab364f |
    | [generated-2.txt](runfiles/generated-2.txt) | file | 9 | ... UTC | 7cbef5232b2e916eccc41d756d05035f |
    | [generated-3.txt](runfiles/generated-3.txt) | file | 7 | ... UTC | 4f6eabeaa60af0c1e30869b32242c615 |
    | link.txt | file link | 6 | ... UTC | 09f7e02f1290be211da707a266f153b3 |
    <BLANKLINE>
    [runfiles.csv](runfiles.csv)
    <BLANKLINE>

Note that `link.txt` does not have a hyperlink. For this we need to
include links when we publish the run.

    >>> quiet(
    ...     f"guild publish ccc --dest={publish_dest} --template=just-files "
    ...      "--all-files --include-links -y"
    ... )

    >>> cat(path(publish_dest, "ccc", "README.md"))
    | Path | Type | Size | Modified | MD5 |
    | ---- | ---- | ---- | -------- | --- |
    | [generated-1.txt](runfiles/generated-1.txt) | file | 5 | ... UTC | 8c8432c5523c8507a5ec3b1ae3ab364f |
    | [generated-2.txt](runfiles/generated-2.txt) | file | 9 | ... UTC | 7cbef5232b2e916eccc41d756d05035f |
    | [generated-3.txt](runfiles/generated-3.txt) | file | 7 | ... UTC | 4f6eabeaa60af0c1e30869b32242c615 |
    | [link.txt](runfiles/link.txt) | file link | 6 | ... UTC | 09f7e02f1290be211da707a266f153b3 |
    <BLANKLINE>
    [runfiles.csv](runfiles.csv)
    <BLANKLINE>

#### Missing link targets

NOTE: This test modifies the run directory for `run_id`.

If the link target is missing (e.g. it was deleted), the table shows
that it's missing.

To illustrate, we'll modify the run link to reference a non-existing
file:

    >>> link_path = path(guild_home, "runs", "ccc", "link.txt")
    >>> os.remove(link_path)
    >>> os.symlink("not-existing", link_path)

When we publish the files list, we see that the link details are
omitted.

    >>> quiet(f"guild publish ccc --dest={publish_dest} --template=just-files -y")

    >>> cat(path(publish_dest, "ccc", "README.md"))
    | Path | Type | Size | Modified | MD5 |
    | ---- | ---- | ---- | -------- | --- |
    | generated-1.txt | file | 5 | ... UTC | 8c8432c5523c8507a5ec3b1ae3ab364f |
    | generated-2.txt | file | 9 | ... UTC | 7cbef5232b2e916eccc41d756d05035f |
    | generated-3.txt | file | 7 | ... UTC | 4f6eabeaa60af0c1e30869b32242c615 |
    | link.txt | link |  |  |  |
    <BLANKLINE>
    [runfiles.csv](runfiles.csv)
    <BLANKLINE>

## Custom runs index

We can specify an alternative index template with `index_template`.

Let's create a new publish target directory.

    >>> publish_dest = mkdtemp()

Publish all of the runs using a custom index template.

    >>> quiet(f"guild publish --dest {publish_dest} --index-template=index-t1 -y")

Show the generated index.

    >>> cat(path(publish_dest, "README.md"))
    A custom runs index!
    <BLANKLINE>
    - [ddd](ddd/README.md) - legacy-sourcecode
    - [ccc](ccc/README.md) - op3
    - [bbb](bbb/README.md) - op2
    - [aaa](aaa/README.md) - op
    <BLANKLINE>

The index template can also be specified as a file.

    >>> quiet(f"guild publish --dest {publish_dest} --index-template=index-t2/TEMPLATE.md -y")

    >>> cat(path(publish_dest, "README.md"))
    Yet another index:
    <BLANKLINE>
    - [ddd](ddd/README.md) - legacy-sourcecode
    - [ccc](ccc/README.md) - op3 c=4
    - [bbb](bbb/README.md) - op2
    - [aaa](aaa/README.md) - op a=1 b=2
    <BLANKLINE>
