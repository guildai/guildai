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

Generate a run for the `default` operation. This operation resolves a
number of dependencies and generates files.

    >>> project.run("default")
    Resolving file:dep-1 dependency
    Resolving file:dep-subdir/dep-2 dependency
    Resolving file:files.zip dependency
    Unpacking .../files.zip
    Generating files

The run files:

    >>> printl(project.ls(all=True))  # doctest: +REPORT_UDIFF
    .guild/attrs/...
    .guild/opref
    .guild/output
    .guild/output.index
    .guild/sourcecode/guild.yml
    .guild/sourcecode/op.py
    .guild/sourcecode/overlap.py
    a
    b
    dep-1
    dep-subdir/dep-2
    subdir/c
    yyy
    zzz

Get a reference to the run, which is used in tests below.

    >>> run = project.list_runs()[0]

## Merge manifest index

`run_merge` uses a run manifest index to help determine how to copy a
run file. This index is generated with
`run_merge._init_manifest_index()`.

    >>> from guild.run_merge import _init_manifest_index

    >>> index = _init_manifest_index(run)

Pretty print the index (file hashes are left in the output to simplify
comparisons on failure - these will change whenever the sample project
source code files, causing this example to fail):

    >>> pprint(index, width=72)  # doctest: +REPORT_UDIFF
    {'.guild/sourcecode/guild.yml': _ManifestEntry(file_type='s', run_path='.guild/sourcecode/guild.yml', file_hash='679abb4272f4e3c9d10c2bcb07b82c6f95f025c1', source='guild.yml', source_subpath=None),
     '.guild/sourcecode/op.py': _ManifestEntry(file_type='s', run_path='.guild/sourcecode/op.py', file_hash='af2386f2c88a0c3c0a55b59008061a0bcf4f0a5a', source='op.py', source_subpath=None),
     '.guild/sourcecode/overlap.py': _ManifestEntry(file_type='s', run_path='.guild/sourcecode/overlap.py', file_hash='11487bbf901e4948ad9505ea3d50d02f28bb8cbe', source='overlap.py', source_subpath=None),
     'dep-1': _ManifestEntry(file_type='d', run_path='dep-1', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:dep-1', source_subpath=None),
     'dep-subdir/dep-2': _ManifestEntry(file_type='d', run_path='dep-subdir/dep-2', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:dep-subdir/dep-2', source_subpath=None),
     'yyy': _ManifestEntry(file_type='d', run_path='yyy', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:files.zip', source_subpath='yyy'),
     'zzz': _ManifestEntry(file_type='d', run_path='zzz', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:files.zip', source_subpath='xxx')}

## Merge files

Files to copy and to skip for a merge are determined in
`run_merge.init_run_merge()`, which returns a `run_merge.RunMerge`
object. `init_run_merge()` accepts a number of configuration
parameters that determine how run files are classified, either to be
copied ro to be skipped.

    >>> from guild.run_merge import init_run_merge

Helper to print merge files.

    >>> def print_mergefiles(run, **opts):
    ...     m = init_run_merge(run, **opts)
    ...     print("To copy:")
    ...     for f in sorted(m.to_copy, key=lambda mf: mf.run_path):
    ...         print(f"[{f.file_type}] {f.run_path} -> {f.target_path}")
    ...     print("To skip:")
    ...     for f in sorted(m.to_skip, key=lambda mf: mf.run_path):
    ...         print(f"[{f.reason}] {f.run_path} -> {f.target_path or '?'}")

By default, source code (files marked with `s`) and project-local
dependencies (files marked with `d`) are copied.

Files that are unpacked from project-local archives are not copied
because these files don't originate from the project directory
itself. Such files are noted as `npd` (non-project dependency) in the
skipped list and don't have a target path.

    >>> print_mergefiles(run)
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Other files (marked with `o`) are not copied by default. These can be
copied by specifying `copy_all=True`.

    >>> print_mergefiles(run, copy_all=True)
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [o] a -> a
    [o] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [o] subdir/c -> subdir/c
    To skip:
    [npd] yyy -> ?
    [npd] zzz -> ?

Source code files can be skipped using `skip_sourecode=True`.

    >>> print_mergefiles(run, skip_sourcecode=True)
    To copy:
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Dependencyes can be skipped using `skip_deps=True`.

    >>> print_mergefiles(run, skip_deps=True)
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    To skip:
    [o] a -> a
    [o] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [o] subdir/c -> subdir/c
    [d] yyy -> ?
    [d] zzz -> ?

Skip both dependencies and source code:

    >>> print_mergefiles(run, skip_deps=True, skip_sourcecode=True)
    To copy:
    To skip:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [o] a -> a
    [o] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [o] subdir/c -> subdir/c
    [d] yyy -> ?
    [d] zzz -> ?

Files can be excluded using patterns in the `exclude` option.

Exclude all files:

    >>> print_mergefiles(run, exclude=("*"))
    To copy:
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [x] .guild/sourcecode/op.py -> op.py
    [x] .guild/sourcecode/overlap.py -> overlap.py
    [o] a -> a
    [o] b -> b
    [x] dep-1 -> dep-1
    [x] dep-subdir/dep-2 -> dep-subdir/dep-2
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

If `copy_all=True`, Guild attempts to copy all files including
'other'. These too can be excluded with `exclude`. In this case, the
reason for skipping is `x` (user-excluded).

    >>> print_mergefiles(run, copy_all=True, exclude=("*"))
    To copy:
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [x] .guild/sourcecode/op.py -> op.py
    [x] .guild/sourcecode/overlap.py -> overlap.py
    [x] a -> a
    [x] b -> b
    [x] dep-1 -> dep-1
    [x] dep-subdir/dep-2 -> dep-subdir/dep-2
    [x] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

In the case of source code files, exclude patterns are applied to the
target path rather than the run path.

    >>> print_mergefiles(run, exclude=("*.py", "*.yml"))
    To copy:
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [x] .guild/sourcecode/op.py -> op.py
    [x] .guild/sourcecode/overlap.py -> overlap.py
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

When we attempt to exclude source code files using run paths, the
files don't match.

    >>> print_mergefiles(run, exclude=(
    ...     ".guild/sourcecode/*.py",
    ...     ".guild/sourcecode/*.yml")
    ... )
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Other exclude patterns:

    >>> print_mergefiles(run, exclude=("a", "subdir/*"))
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

    >>> print_mergefiles(run, copy_all=True, exclude=("a", "subdir/*"))
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [o] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [x] a -> a
    [x] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

    >>> print_mergefiles(run, exclude=("guild.yml", "dep-*"))
    To copy:
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [o] a -> a
    [o] b -> b
    [x] dep-1 -> dep-1
    [x] dep-subdir/dep-2 -> dep-subdir/dep-2
    [o] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

    >>> print_mergefiles(run, copy_all=True, exclude=("guild.yml", "dep-*"))
    To copy:
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [x] dep-1 -> dep-1
    [x] dep-subdir/dep-2 -> dep-subdir/dep-2
    [npd] yyy -> ?
    [npd] zzz -> ?

## Merge file

To apply a merge, use `run_merge.appyly_run_merge`.

    >> from guild.run_merge import apply_run_merge

Merges are applied to a target directory.

    >> target_dir = mkdtemp()
    >> apply_run_merge(RunMerge(run), target_dir)

    >> find(target_dir)
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py
    subdir/c

Compare the original project directory with the target directory.

    >> import filecmp
    >> filecmp.dircmp(sample, target_dir).report()
    diff ...
    Only in .../samples/projects/merge : ['.gitignore', 'files.zip']
    Identical files : ['a', 'b', 'dep-1', 'guild.yml', 'op.py', 'overlap.py']
    Common subdirectories : ['dep-subdir', 'subdir']

<a id="prune">

## Pruning overlapping merge files

It's possible that a list of merge files for a merge contains
overlapping target paths. This occurs when a project file is copied to
a run both as source code and as a dependency - or copied as source
code and generated by the run.

Consider the following run directlry layout:

```
./.guild/sourcecode/foo.txt
./foo.txt
```

This occurs when the file `foo.txt` is specified as project local file
dependency and selected as source code. This Guild file shows how this
might occur.

``` yaml
op:
  requires:
    - file: foo.txt
```

If `foo.txt` meets Guild's default criteria for source code select,
the run will contain the same project file `foo.txt` as both source
code and non-source code.

The function `run_merge.prune_overlapping_targets()` is used to remove
duplicate merge files from a runs merge based on a preference: keep
source code files or keep non-source code files.

    >> from guild.run_merge import prune_overlapping_targets

Helper to test pruning.

    >> def prune(files, prefer_nonsource=False):
    ...     from guild.run_merge import MergeFile
    ...     merge_files = [
    ...         MergeFile(type=type, run_path=None, target_path=target)
    ...         for type, target in files
    ...     ]
    ...     merge = RunMerge(None, files=merge_files)
    ...     prune_overlapping_targets(merge, prefer_nonsource)
    ...     return [(mf.type, mf.target_path) for mf in merge.files]

Empty case:

    >> prune([])
    []

Non overlapping:

    >> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt")
    ... ])
    [('s', 'foo.txt'), ('d', 'bar.txt')]

    >> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt")
    ... ],
    ... prefer_nonsource=True)
    [('s', 'foo.txt'), ('d', 'bar.txt')]

Overlapping source code and dependency:

    >> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "foo.txt")
    ... ])
    [('s', 'foo.txt')]

    >> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "foo.txt")
    ... ],
    ... prefer_nonsource=True)
    [('d', 'foo.txt')]

Overlapping source code and generated:

    >> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt"),
    ...     ("g", "foo.txt")
    ... ])
    [('s', 'foo.txt'), ('d', 'bar.txt')]

    >> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt"),
    ...     ("g", "foo.txt")
    ... ],
    ... prefer_nonsource=True)
    [('d', 'bar.txt'), ('g', 'foo.txt')]
