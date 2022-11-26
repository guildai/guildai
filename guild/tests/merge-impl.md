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
    ...     rmdir(path(project_dir, "subdir"), force=True)
    ...     rmdir(path(project_dir, "__pycache__"), force=True)

    >>> clean_project()

Project files:

    >>> find(project_dir)
    .gitignore
    dep-1
    dep-subdir/dep-2
    files.zip
    guild.yml
    op.py
    overlap.py

Create a new Guild home to isolate runs.

    >>> guild_home = mkdtemp()

Helpers to run commands from the project dir and with `GUILD_HOME` set
for Guild commands.

    >>> def project_run(cmd, **kw):
    ...     run(cmd, cwd=project_dir, env={"GUILD_HOME": guild_home}, **kw)

    >>> def project_quiet(cmd, **kw):
    ...     quiet(cmd, cwd=project_dir, env={"GUILD_HOME": guild_home}, **kw)

    >>> def project_capture(cmd, **kw):
    ...     out, code = run_capture(cmd, cwd=project_dir,
    ...                             env={"GUILD_HOME": guild_home}, **kw)
    ...     assert code == 0, (code, out)
    ...     return out

Verify the project ops.

    >>> project_run("guild ops")
    default
    overlap
    remote-dep
    <exit 0>

## Generate a run

Generate a run from the sample project.

    >>> project_run("guild run default -y")
    Resolving file:dep-1
    Resolving file:dep-subdir/dep-2
    Resolving file:files.zip
    Unpacking .../files.zip
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
        - yyy
        - zzz
      sourcecode:
        - guild.yml
        - op.py
        - overlap.py
    <exit 0>

    >>> project_run("guild ls -n")
    a
    b
    dep-1
    dep-subdir/
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py
    subdir/
    subdir/c
    yyy
    zzz
    <exit 0>

## Non-VCS behavior

Guild only copies files that are unchanged. If a project is not under
version control, Guild will not copy any files unless the '--replace'
option is specified.

As there are no differences between the run files (those to be copied)
and the project files, the merge command completes without an error
but with a message indicating that nothing is copied.

    >>> project_run("guild merge -y")
    Nothing to copy for the following run:
      [...]  default  ...  completed
    Try 'guild merge --preview' for a list of skipped files.
    <exit 0>

Show the skipped files using the '--preview' option.

    >>> project_run("guild merge --preview")  # doctest: +REPORT_UDIFF
    Merge will copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files:
      nothing to copy
    Skipped:
      a                 non-project file
      b                 non-project file
      dep-1             unchanged
      dep-subdir/dep-2  unchanged
      guild.yml         unchanged
      op.py             unchanged
      overlap.py        unchanged
      subdir/c          non-project file
      yyy               non-project dependency
      zzz               non-project dependency
    <exit 0>

Let's modify some of the project files.

    >>> write(path(project_dir, "dep-1"), "xxx")
    >>> write(path(project_dir, "dep-subdir", "dep-2"), "yyy")

    >>> run_dir = project_capture("guild select --path")
    >>> compare_dirs((run_dir, "run-dir"), (project_dir, "project-dir"))
    diff /run-dir /project-dir
    Only in /run-dir : ['.guild', 'a', 'b', 'subdir', 'yyy', 'zzz']
    Only in /project-dir : ['.gitignore', 'files.zip']
    Identical files : ['guild.yml', 'op.py', 'overlap.py']
    Differing files : ['dep-1']
    Common subdirectories : ['dep-subdir']
    <BLANKLINE>
    diff /run-dir/dep-subdir /project-dir/dep-subdir
    Differing files : ['dep-2']

    >>> cat(path(project_dir, "dep-1"))
    xxx

    >>> cat(path(project_dir, "dep-subdir", "dep-2"))
    yyy

If a project is not under version control, Guild maintains a strict
no-replace policy for all copied files. When we attempt a merge now,
we get an error.

    >>> project_run("guild merge -y")
    guild: files in the current directory would be replaced:
      dep-1
      dep-subdir/dep-2
    Use --replace to skip this check.
    <exit 1>

This error is shown as well with the '--preview' option.

    >>> project_run("guild merge --preview")
    guild: files in the current directory would be replaced:
      dep-1
      dep-subdir/dep-2
    Use --replace to skip this check.
    <exit 1>

If we include '--replace' along with '--preview', Guild shows the two
project-local dependencies as the files to-be-copied.

    >>> project_run("guild merge --preview --replace")
    Merge will copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files:
      dep-1
      dep-subdir/dep-2
    Skipped:
      a           non-project file
      b           non-project file
      guild.yml   unchanged
      op.py       unchanged
      overlap.py  unchanged
      subdir/c    non-project file
      yyy         non-project dependency
      zzz         non-project dependency
    <exit 0>

To perform the merge, use the '--replace' without preview.

    >>> project_run("guild merge --replace -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    <exit 0>

Compare files after the merge.

    >>> compare_dirs((run_dir, "run-dir"), (project_dir, "project-dir"))
    diff /run-dir /project-dir
    Only in /run-dir : ['.guild', 'a', 'b', 'subdir', 'yyy', 'zzz']
    Only in /project-dir : ['.gitignore', 'files.zip']
    Identical files : ['dep-1', 'guild.yml', 'op.py', 'overlap.py']
    Common subdirectories : ['dep-subdir']
    <BLANKLINE>
    diff /run-dir/dep-subdir /project-dir/dep-subdir
    Identical files : ['dep-2']

    >>> cat(path(project_dir, "dep-1"))
    <empty>

    >>> cat(path(project_dir, "dep-subdir", "dep-2"))
    <empty>

### Merging to an empty directory

Merging into an empty directory poses no replacement issues.

Create a temp directory for our various merge targets.

    >>> tmp = mkdtemp()

Merge only source code and depepdencies (default behavior):

    >>> project_run(f"guild merge -t {tmp}/default -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying guild.yml
    Copying op.py
    Copying overlap.py
    <exit 0>

    >>> find(f"{tmp}/default")
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py

Merge sourcecode only:

    >>> project_run(f"guild merge --sourcecode -t {tmp}/sourcecode -y")
    Copying guild.yml
    Copying op.py
    Copying overlap.py
    <exit 0>

    >>> find(f"{tmp}/sourcecode")
    guild.yml
    op.py
    overlap.py

Merge deps only (skip source code):

    >>> project_run(f"guild merge --skip-sourcecode -t {tmp}/deps -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    <exit 0>

    >>> find(f"{tmp}/deps")
    dep-1
    dep-subdir/dep-2

Merge only generated by including all and skipping both source code
and dependencies:

    >>> project_run(f"guild merge --all --skip-sourcecode --skip-deps -t {tmp}/generated -y")
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

Attempt to merge with unchanged files.

    Nothing to copy for the following run:
      [...]  default  ...  completed
    Try 'guild merge --preview' for a list of skipped files.
    <exit 0>

Modify local project files.

    >>> write(path(project_dir, "dep-1"), "xxx")
    >>> write(path(project_dir, "dep-subdir", "dep-2"), "yyy")
    >>> write(path(project_dir, "op.py"), "print('hi')\n")

Preview the merge.

    >>> project_run("guild merge --preview")
    guild: files in the current directory have unstaged changes:
      dep-1
      dep-subdir/dep-2
      op.py
    Stage or stash these changes or use --replace to skip this check.
    <exit 1>

Attempt the merge.

    >>> project_run("guild merge -y")
    guild: files in the current directory have unstaged changes:
      dep-1
      dep-subdir/dep-2
      op.py
    Stage or stash these changes or use --replace to skip this check.
    <exit 1>

Guild shows a different message because the project is managed under a
VCS (git in this case).

Stage the changes and try again. Guild copies the files because
they're staged.

    >>> project_quiet("git add .")

Preview the merge.

    >>> project_run("guild merge --preview")
    Merge will copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files:
      dep-1
      dep-subdir/dep-2
      op.py
    Skipped:
      a           non-project file
      b           non-project file
      guild.yml   unchanged
      overlap.py  unchanged
      subdir/c    non-project file
      yyy         non-project dependency
      zzz         non-project dependency
    <exit 0>

    >>> project_run("guild merge -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying op.py
    <exit 0>

Now that the project is merged with the run changes, there's nothing
to copy on a subsequent merge.

    >>> project_run("guild merge -y")
    Nothing to copy for the following run:
      [...]  default  ...  completed
    Try 'guild merge --preview' for a list of skipped files.
    <exit 0>

Let's restore the project to its staged stage.

    >>> project_quiet("git restore .")

When we merge, Guild copies the project files as before because the
project is safely staged.

    >>> project_run("guild merge -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying op.py
    <exit 0>

Let's restore again and then commit the changes.

    >>> project_quiet("git restore .")
    >>> project_quiet("git commit -m 'First commit'")

    >>> project_run("guild merge --preview")
    Merge will copy files from the following run to the current directory:
      [...]  default  ...  completed
    Files:
      dep-1
      dep-subdir/dep-2
      op.py
    Skipped:
      a           non-project file
      b           non-project file
      guild.yml   unchanged
      overlap.py  unchanged
      subdir/c    non-project file
      yyy         non-project dependency
      zzz         non-project dependency
    <exit 0>

    >>> project_run("guild merge -y")
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying op.py
    <exit 0>

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
    guild: run ... was created from a different project (...) - cannot merge
    to the current directory by default
    Use '--target-dir .' to override this check or try 'guild merge --help'
    for more information.
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
    Skip this check by using --target-dir
    <exit 1>

## Overlapping targets

It's possible in Guild to have multiple run files that map to the same
project target. For details, see [merge.md](merge.md#prune).

The `overlap` operation creates a target path overlap example.

- Project local dependencies overlap with source code files
- The operation overwrites one of the overlapped files with generated
  content

    >>> project_run("guild run overlap -y")
    Resolving file:dep-1
    Resolving file:dep-subdir/dep-2
    Generating files
    <exit 0>

When a dependency collides with a source code file, Guild treats the
file as a dependency, not a source code file.

If a generated file replaces an existing file, Guild does not consider
that file generated - the manifest entry is used as the authoritative
designation of the file type.

    >>> project_run("guild cat -p .guild/manifest")
    s guild.yml ... guild.yml
    s op.py ... op.py
    s overlap.py ... overlap.py
    d dep-1 ... file:dep-1
    d dep-subdir/dep-2 ... file:dep-subdir/dep-2
    <exit 0>

The run file `dep-1` is modified by the operation.

    >>> project_run("guild cat -p dep-1")
    generated!
    <exit 0>

    >>> cat(path(project_dir, "dep-1"))
    <empty>

When we merge such a run, Guild gives preference to non-source code
files. Note the user may either prefer to copy the source code or to
be notified of this case with a warning or error that requires an
option to disable the check.

At this time, however, Guild prefers non-source files when merging for
the following reasons:

- In the case of overlapping source and project-local dependencies,
  the files will be the same and it won't matter which file is
  selected for the merge.

- Source code files are already protected by Guild's VCS status
  check. If an unexpected overlap occurs, the user can correct the
  problem by filtering out the dependency in the Guild file sourcecode
  spec.

- In the case where a source code file overlaps with a generated file,
  the generated file may be presumed as preferrable as it's the most
  recent version of the file.

At this point `dep-1` is modified by the generated file. We can't
merge unless we specify either '--replace' or stage/stash the changes.

    >>> project_run("guild merge -y")
    guild: files in the current directory have unstaged changes:
      dep-1
    Stage or stash these changes or use --replace to skip this check.
    <exit 1>

Let's use '--replace' to ignore the VCS status check.

    >>> project_run("guild merge --replace -y")
    Copying dep-1
    <exit 0>

We can use git to view changes to the project.

    >>> project_run("git status -s")
    M dep-1
     M dep-subdir/dep-2
     M op.py
    <exit 0>

    >>> cat(path(project_dir, "dep-1"))
    generated!

# TODO

- Diff option (like preview but uses configured diff tool to show
  differences)

- Run summary to `guild-run-summary.json` (or specified by
  --summary-name) - to be skipped with --skip-summary
