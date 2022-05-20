# Guild Merge

`guild merge` is used to copy files from a run directory into a
working directory.

We use the [`merge`](samples/projects/merge) project for the tests
below.

    >>> sample = sample("projects", "merge")

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

### Files to copy

By default, Guild copies the source code and generated files on
merge. We can get a list of these files using
`guild.run_merge.RunMerge`.

    >>> from guild.run_merge import RunMerge

Helper to print merge files.

    >>> def print_mergefiles(m):
    ...     for f in sorted(m.files, key=lambda mf: mf.run_path):
    ...         print(f"[{f.type}] {f.run_path} -> {f.project_path}")

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
