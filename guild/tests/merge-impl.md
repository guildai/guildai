# Merge Implementation

These tests cover lower level behavior in `guild.commands.merge_impl`.

In particular, we test behavior related to file replacement in the
merge target directory. It's critical that this behavior is correct as
it exposes the user project to corruption.

## Project and Guild env init

Create a new project that we can freely modify without changing test
code.

    >>> project_dir = mkdtemp()
    >>> copytree(sample("projects", "merge"), project_dir)

Remove ignored files if they exit. Use a helper function so we can run
this as needed.

    >>> def clean_project():
    ...     rm(path(project_dir, "a"), force=True)
    ...     rm(path(project_dir, "b"), force=True)
    ...     rmdir(path(project_dir, "subdir"))

    >>> clean_project()

Project files:

    >>> find(project_dir)
    .gitignore
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py

Create a new Guild home to isolate runs.

    >>> guild_home = mkdtemp()

Helpers to run commands from the project dir and with `GUILD_HOME` set
for Guild commands.

    >>> def project_run(cmd, **kw):
    ...     run(cmd, cwd=project_dir, env={"GUILD_HOME": guild_home}, **kw)

    >>> def project_quiet(cmd, **kw):
    ...     quiet(cmd, cwd=project_dir, env={"GUILD_HOME": guild_home}, **kw)

Verify the project ops.

    >>> project_run("guild ops")
    default
    <exit 0>

## Generate a run

Generate a run from the sample project.

    >>> project_run("guild run default -y")
    Resolving file:dep-1 dependency
    Resolving file:dep-subdir/dep-2 dependency
    Generating files
    <exit 0>

    >>> project_run("guild runs")
    [1:...]  default  ...  completed
    <exit 0>

    >>> project_run("guild runs info --manifest")
    id: ...
    operation: default
    from: .../guild.yml
    status: completed
    ...
    manifest:
      dependencies:
        - dep-1
        - dep-subdir/dep-2
      sourcecode:
        - .guild/sourcecode/guild.yml
        - .guild/sourcecode/op.py
    <exit 0>

    >>> project_run("guild ls -n")
    a
    b
    dep-1
    dep-subdir/
    dep-subdir/dep-2
    subdir/
    subdir/c
    <exit 0>

## Non-VCS behavior

If a project is not under version control, Guild maintains a strict
no-replace policy for all merged/copied files.

Attempt to merge the run.

    >>> project_run("guild merge -y")
    guild: files in the current directory would be replaced:
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
    Use --replace to skip this check.
    <exit 1>

Override Guild's policy by specifying the '--replace' option.

Preview the merge command.

    >>> project_run("guild merge --replace", timeout=2)
    You are about to copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files to copy:
      a
      b
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
      subdir/c
    Continue (y/N)? (y/N)
    <exit ...>

Run the command.

    >>> project_run("guild merge --replace -y")
    Copying a
    Copying b
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying guild.yml
    Copying op.py
    Copying subdir/c
    <exit 0>

Project files:

    >>> find(project_dir)
    .gitignore
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    subdir/c

Merging into an empty directory poses no replacement issues.

Create a temp directory for our various merge targets.

    >>> tmp = mkdtemp()

Merge everything:

    >>> project_run(f"guild merge -t {tmp}/everything -y")
    Copying a
    Copying b
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying guild.yml
    Copying op.py
    Copying subdir/c
    <exit 0>

    >>> find(f"{tmp}/everything")
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    subdir/c

Merge sourcecode only:

    >>> project_run(f"guild merge -s -t {tmp}/sourcecode -y")
    Copying guild.yml
    Copying op.py
    <exit 0>

    >>> find(f"{tmp}/sourcecode")
    guild.yml
    op.py

Merge deps only:

    >>> project_run(f"guild merge -SG -t {tmp}/deps -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    <exit 0>

    >>> find(f"{tmp}/deps")
    dep-1
    dep-subdir/dep-2

Merge generated only:

    >>> project_run(f"guild merge -SD -t {tmp}/generated -y")
    Copying a
    Copying b
    Copying subdir/c
    <exit 0>

    >>> find(f"{tmp}/generated")
    a
    b
    subdir/c

## VCS behavior

Guild applies a different policy when a project (or target directory)
is configured with a VCS.

Initialize a git repositiry in the project directory.

    >>> project_quiet("git init")

Remove deps and generated files (from previous merges).

    >>> clean_project()

Attempt to merge.

    >>> project_run("guild merge -y")
    guild: files in the current directory have uncommitted changes:
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
    Commit these changes or use --replace to skip this check.
    <exit 1>

Commit the changes.

    >>> project_quiet("git add .")
    >>> project_quiet("git commit -m 'First commit'")

Attempt to merge again. This succeeds because we're replacing files
that are committed.

    >>> project_run("guild merge -y")
    Copying a
    Copying b
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying guild.yml
    Copying op.py
    Copying subdir/c
    <exit 0>

Our project now has additional files from the run -- dependencies and
generated files.

    >>> find(project_dir)
    .git/...
    .gitignore
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    subdir/c

    >>> project_run("guild merge -y")
    guild: files in the current directory would be replaced:
      a
      b
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
      subdir/c
    Use --replace to skip this check.
    <exit 1>

These three files are explicitly ignored by git.

    >>> cat(path(project_dir, ".gitignore"))
    a
    b
    subdir/c

In this case, the user has a several options:

- Use the '--replace' option, which disables Guild's replacement
  checks
- Use both '--skip-deps' and '--skip-generated' options, which skips
  the copying of the dependencies and generated files
- Use the '--sourcecode' option to only copy soure code files (this
  implies use of both '--skip-deps' and '--skip-generated')
- Exclude the conflicting files using '--exclude'
- Merge to a different directory that doesn't contain the conflicting
  files

Let's use each of these options with a preview message (won't actually
copy anything).

Use '--replace':

    >>> project_run("guild merge --replace", timeout=2)
    You are about to copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files to copy:
      a
      b
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
      subdir/c
    Continue (y/N)? (y/N)
    <exit ...>

Use '--skip-deps' and '--skip-generated':

    >>> project_run("guild merge --skip-deps --skip-generated", timeout=2)
    You are about to copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files to copy:
      guild.yml
      op.py
    Continue (y/N)? (y/N)
    <exit ...>

Use '--sourcecode':

    >>> project_run("guild merge --sourcecode", timeout=2)
    You are about to copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files to copy:
      guild.yml
      op.py
    Continue (y/N)? (y/N)
    <exit ...>

Exclude the offending files:

    >>> project_run("guild merge -x a -x b -x '*/c'", timeout=2)
    You are about to copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files to copy:
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
    Continue (y/N)? (y/N)
    <exit ...>

Merge to a different directory:

    >>> tmp = mkdtemp()

    >>> project_run(f"guild merge --target-dir '{tmp}'", timeout=2)
    You are about to copy files from the following run to '...':
      [...]  default  ...  completed
    Files to copy:
      a
      b
      dep-1
      dep-subdir/dep-2
      guild.yml
      op.py
      subdir/c
    Continue (y/N)? (y/N)
    <exit ...>

## Default directory checks

By default Guild copies run files to the Guild current working
directory (either the process cwd or the dir specified with the `-C`
option to the `guild` command). If the user wants to copy run files to
a different directory, they can specify the '--target-dir' option.

Guild checks that the current directory is associated with the merged
run. The merge command exits with an error message if not.

There are two cases where Guild generates an error message:

1. The run is not associated with a project (pkg type is not
   'guildfile' or 'script')

2. The project directory for the run is different from the current
   directory

For the tests below we use a helper for creating a run with
configurable opref info.

    >>> def init_run(pkg_type, pkg_name, op_name):
    ...     from guild import op as oplib
    ...     from guild import opref
    ...     from guild import run as runlib
    ...     from guild import util
    ...
    ...     op = oplib.Operation()
    ...     op.opref = opref.OpRef(pkg_type, pkg_name, "", "", op_name)
    ...     run = oplib.init_run(op, path(guild_home, "runs", runlib.mkid()))
    ...     util.touch(path(run.guild_path("manifest")))
    ...     return run

### Case 1 - run is not Guild file or script based

Create a run that's not associated with a project.

    >>> _ = init_run("func", "", "hello")
    >>> project_run("guild runs -n1")
    [1:...]  hello()    pending
    <exit 0>

The run pkg type 'func' in the run opdef indicates the run does not
originate from a project directory.

    >>> project_run("guild cat -p .guild/opref")
    func:'' '' '' hello
    <exit 0>

Attempt to merge the run. We safegaurd accidental copies by using an
empty cwd for the test.

    >>> run(f"guild -H {guild_home} merge 1 -y", cwd=mkdtemp())
    guild: run ... does not originate from a project - cannot merge to the
    current directory by default
    Use --target-dir to skip this check or try 'guild merge --help' for more
    information.
    <exit 1>

### Case 2 - project directory is different from cwd

We test Guild using two cases:

2.1. The cwd is different from the project directory (common case)

2.2. The run is guildfile or script based but Guild can't determine
     the project directory (pathological case indicating a possible
     bug in Guild)

Generate a new run from the project dir.

    >>> project_quiet("guild run default -y")

Attempt to merge from a new, empty directory.

    >>> tmp = mkdtemp()
    >>> run(f"guild -H {guild_home} merge -y", cwd=tmp)
    guild: run ... originates from a different directory (...) - cannot merge
    to the current directory by default
    Use --target-dir to override this check or try 'guild merge --help' for more information.
    <exit 1>

Next we test the pathological case where Guild can't determine a
project directory from a Guild file based run.

Create a pathological/broken run where the pkg_name is empty.

    >>> _ = init_run("guildfile", "", "broken")
    >>> project_run("guild cat -p .guild/opref")
    guildfile:'' '' '' broken
    <exit 0>

    >>> project_run("guild runs -n1")
    [1:...]  broken    pending
    <exit 0>

Attempt to merge this run to tmp.

    >>> run(f"guild -H {guild_home} merge -y", cwd=tmp)
    guild: unexpected missing project directory for run ... (guildfile:''
    '' '' broken)
    This may be a bug in Guild - please report to
    https://github.com/guildai/guildai/issues
    Skip this check by using --target-dir
    <exit 1>

# TODO

- Run summary to `guild-run-summary.json` (or specified by
  --summary-name) - to be skipped with --skip-summary

- Consider not copying generated by default (support with --generated
  and include patterns)
