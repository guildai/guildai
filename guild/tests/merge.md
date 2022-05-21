# Guild Merge

`guild merge` is used to copy files from a run directory into a
working directory.

We use the [`merge`](samples/projects/merge) project for the tests
below.

    >>> sample = sample("projects", "merge")

Rename the run command as we use 'run' below.

    >>> run_ = run

## Default behavior

By default, Guild copies run files into the project directory.

A merge consists of a copy of:

- Run source code files to the applicable source code directory in the
  project
- Copy of local file dependencies originating from the project
  directory
- Copy generated files
- Generated summary of the run `guild-run-summary.json`

Optional behavior (covered below) includes:

- Don't copy source code
- Don't copy dependencies
- Don't copy generated files
- Exclude specific files using one or more wildcard expressions
- Copy files to a different directory (required if the run is not from
  a local, existing Guild project)
- Don't generate a run summary
- When generating a summary, use a name that includes the run ID

Because these tests modify the project directory, we create a copy of
the sample project to a temp location.

    >>> tmp = mkdtemp()
    >>> copytree(sample, tmp)
    >>> project = Project(tmp)

Generate a run.

    >>> project.run("default")
    Resolving file:dep-1 dependency
    Resolving file:dep-subdir/dep-2 dependency
    Generating files

The run files:

    >>> printl(project.ls(all=True))  # doctest: +REPORT_UDIFF
    .guild/attrs/...
    .guild/opref
    .guild/output
    .guild/output.index
    .guild/sourcecode/guild.yml
    .guild/sourcecode/op.py
    a
    b
    dep-1
    dep-subdir/dep-2
    subdir/c

## Merge files

By default, Guild copies the source code and generated files on
merge. We can get a list of these files using
`guild.run_merge.RunMerge`.

    >>> from guild.run_merge import RunMerge

Helper to print merge files.

    >>> def print_mergefiles(m):
    ...     for f in sorted(m.files, key=lambda mf: mf.run_path):
    ...         print(f"[{f.type}] {f.run_path} -> {f.target_path}")

Get the latest run.

    >>> run = project.list_runs()[0]

By default, sourcecode, deps, and generated files are copied.

    >>> print_mergefiles(RunMerge(run))
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [g] a -> a
    [g] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [g] subdir/c -> subdir/c

Skip sourcecode files:

    >>> print_mergefiles(RunMerge(run, skip_sourcecode=True))
    [g] a -> a
    [g] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [g] subdir/c -> subdir/c

Skip dependencies:

    >>> print_mergefiles(RunMerge(run, skip_deps=True))
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [g] a -> a
    [g] b -> b
    [g] subdir/c -> subdir/c

Skip generated:

    >>> print_mergefiles(RunMerge(run, skip_generated=True))
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2

Skip all run file types:

    >>> print_mergefiles(RunMerge(run,
    ...                           skip_sourcecode=True,
    ...                           skip_deps=True,
    ...                           skip_generated=True))

Filter by file patterns:

    >>> print_mergefiles(RunMerge(run, exclude=("*")))

    >>> print_mergefiles(RunMerge(run, exclude=("*.py", "*.yml")))
    [g] a -> a
    [g] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [g] subdir/c -> subdir/c

    >>> print_mergefiles(RunMerge(run, exclude=("a", "subdir/*")))
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [g] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2

    >>> print_mergefiles(RunMerge(run, exclude=("guild.yml", "dep-*")))
    [s] .guild/sourcecode/op.py -> op.py
    [g] a -> a
    [g] b -> b
    [g] subdir/c -> subdir/c

## Merge file

To apply a merge, use `run_merge.appyly_run_merge`.

    >>> from guild.run_merge import apply_run_merge

Merges are applied to a target directory.

    >>> target_dir = mkdtemp()
    >>> apply_run_merge(RunMerge(run), target_dir)

    >>> find(target_dir)
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    subdir/c

Compare the original project directory with the target directory.

    >>> import filecmp
    >>> filecmp.dircmp(sample, target_dir).report()
    diff ...
    Only in .../samples/projects/merge : ['.gitignore']
    Identical files : ['a', 'b', 'dep-1', 'guild.yml', 'op.py']
    Common subdirectories : ['dep-subdir', 'subdir']

## Default directory checks

By default Guild copies run files to the current working directory. If
the user wants to copy run files to a different directory, they can
specify the --target-dir option.

Guild check that the current directory is associated with the merged
run. The merge command exits with an error message if not.

There are two cases where Guild generates an error message:

- Run is not associated with a project (pkg type is not 'guildfile' or
  'script')
- Project directory for the run is different from the current
  directory

For the tests below we use a helper for creating a run with
configurable opref info.

    >>> def init_run(pkg_type, pkg_name, op_name):
    ...     from guild import op as oplib
    ...     from guild import opref
    ...     from guild import run as runlib
    ...     from guild import util
    ...     op = oplib.Operation()
    ...     op.opref = opref.OpRef(pkg_type, pkg_name, "", "", op_name)
    ...     run = oplib.init_run(op, path(project.guild_home, "runs", runlib.mkid()))
    ...     util.touch(path(run.guild_path("manifest")))
    ...     return run

### Run is not Guild file or script based

Create a run that's not associated with a project.

    >>> run = init_run("func", "", "hello")
    >>> project.print_runs(limit=1)
    hello()

The run pkg type indicates the run does not originate from a project
directory.

    >>> run.opref.pkg_type
    'func'

Attempt to merge the run. We safegaurd accidental copies by using an
empty cwd for the test.

    >>> tmp = mkdtemp()
    >>> run_(f"guild -H {project.guild_home} merge 1 -y", cwd=tmp)
    guild: run ... does not originate from a project - cannot merge to the
    current directory by default
    Specify --target-dir to skip this check or try 'guild merge --help'
    for more information.
    <exit 1>

### Project directory is different from cwd

We test Guild using two cases:

- The cwd is different from the project directory (common case)
- The run is guildfile or script based but Guild can't determine the
  project directory (pathological case indicating a possible bug in
  Guild)

Attempt the second run ('default' from our tests above) to merge from
an empty tmp directory.

First verify that tmp is empty and not the project directory.

    >>> find(tmp)
    <empty>

    >>> from guild import util
    >>> util.compare_paths(tmp, project.cwd)
    False

Confirm that we're attempting to merge the 'default' run from above.

    >>> run = project.list_runs()[1]
    >>> run.opref
    OpRef(pkg_type='guildfile', pkg_name='.../guild.yml',
          pkg_version='...', model_name='', op_name='default')

Attempt to merge from a directory that's different from the project
directory.

    >>> run_(f"guild -H {project.guild_home} merge {run.id} -y", cwd=tmp)
    guild: run ... originates from a different directory (...) - cannot merge
    to the current directory by default
    Specify --target-dir to override this check or try 'guild merge --help'
    for more information.
    <exit 1>

Next we test the pathological case where Guild can't determine a
project directory from a Guild file based run.

Create a pathological/broken run where the pkg_name is empty.

    >>> run = init_run("guildfile", "", "broken")
    >>> run.opref
    OpRef(pkg_type='guildfile', pkg_name='', pkg_version='', model_name='',
          op_name='broken')

    >>> project.print_runs(limit=1)
    broken

Attempt to merge this run to tmp.

    >>> run_(f"guild -H {project.guild_home} merge {run.id} -y", cwd=tmp)
    guild: unexpected missing project directory for run ...
    (guildfile:'' '' '' broken)
    This may be a bug in Guild - please report to
    https://github.com/guildai/guildai/issues
    Skip this check by specifying --target-dir
    <exit 1>

## TODO / Notes

### Backup replaced files

How to handle backups? We can't risk destroying useful information and
so must create restorable backups whenever we overwrite a file.

A few ideas:

1. Backup alongside the replaced file using a special suffix
   (e.g. `*.<run ID or date or version>.guild-merge`)
2. Backup under a project-local `.guild/merge-backups` directory
3. Backup outside the project directory to `$GUILD_HOME/merge-backups`

Option 1 is simple enough but it clutters the working directory and
might incent the user to use a `--no-backup` option to avoid the
clutter.

Option 2 seems the most sensible. The project-local files are in the
project directory itself (no chance of being orphaned if the project
is deleted or removed) and can be easily enumerated.

Option 3 avoid touching the project at all. It's similar to flags
import caching. It has the problem of leaving backups around when the
project directory is deleted. It also suffers from orphaning backups
if the project directory is renamed/moved.
