# Guild Merge

These tests cover `guild.run_merge` at the library level. For `merge`
command testing, see [`merge-impl.md`](merge-impl.md).

We use the [`merge`](samples/projects/merge) project for the tests
below.

    >>> sample = sample("projects", "merge")

Because these tests may modify the project directory, we create a copy
of the sample project to a temp location.

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
