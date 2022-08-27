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

We generate a run for the `default` operation. This operation resolves a number
of dependencies and generates files.

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

We pretty print the index. Note that file hashes are left in the output to
simplify comparisons on failure - these will change whenever the sample project
source code files, causing this example to fail. Note also that paths are
normalized to use '/' path delimiters.

    >>> pprint(index, width=72)  # doctest: +REPORT_UDIFF -NORMALIZE_PATHS
    {'.guild/sourcecode/guild.yml': _ManifestEntry(file_type='s', run_path='.guild/sourcecode/guild.yml', file_hash='679abb4272f4e3c9d10c2bcb07b82c6f95f025c1', source='guild.yml', source_subpath=None),
     '.guild/sourcecode/op.py': _ManifestEntry(file_type='s', run_path='.guild/sourcecode/op.py', file_hash='af2386f2c88a0c3c0a55b59008061a0bcf4f0a5a', source='op.py', source_subpath=None),
     '.guild/sourcecode/overlap.py': _ManifestEntry(file_type='s', run_path='.guild/sourcecode/overlap.py', file_hash='11487bbf901e4948ad9505ea3d50d02f28bb8cbe', source='overlap.py', source_subpath=None),
     'dep-1': _ManifestEntry(file_type='d', run_path='dep-1', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:dep-1', source_subpath=None),
     'dep-subdir/dep-2': _ManifestEntry(file_type='d', run_path='dep-subdir/dep-2', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:dep-subdir/dep-2', source_subpath=None),
     'yyy': _ManifestEntry(file_type='d', run_path='yyy', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:files.zip', source_subpath='yyy'),
     'zzz': _ManifestEntry(file_type='d', run_path='zzz', file_hash='da39a3ee5e6b4b0d3255bfef95601890afd80709', source='file:files.zip', source_subpath='xxx')}

## Merge files to copy

Files to copy and to skip for a merge are determined in
`run_merge.init_run_merge()`, which returns a `run_merge.RunMerge`
object. `init_run_merge()` accepts a number of configuration
parameters that determine how run files are classified, either to be
copied ro to be skipped.

    >>> from guild.run_merge import init_run_merge

Helper to print merge files.

    >>> def print_merge(merge):
    ...     print("To copy:")
    ...     for f in sorted(merge.to_copy, key=lambda mf: mf.run_path):
    ...         print(f"[{f.file_type}] {f.run_path} -> {f.target_path}")
    ...     print("To skip:")
    ...     for f in sorted(merge.to_skip, key=lambda mf: mf.run_path):
    ...         print(f"[{f.reason}] {f.run_path} -> {f.target_path or '?'}")

By default, source code (files marked with `s`) and project-local
dependencies (files marked with `d`) are copied.

Files that are unpacked from project-local archives are not copied
because these files don't originate from the project directory
itself. Such files are noted as `npd` (non-project dependency) in the
skipped list and don't have a target path.

Create an empty target directory.

    >>> empty_dir = mkdtemp()

Print the files that Guild copies by default.

    >>> print_merge(init_run_merge(run, empty_dir))
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [?] a -> a
    [?] b -> b
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Other files (marked with `o`) are not copied by default. These can be
copied by specifying `copy_all=True`.

    >>> print_merge(init_run_merge(run, empty_dir, copy_all=True))
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

    >>> print_merge(init_run_merge(run, empty_dir, skip_sourcecode=True))
    To copy:
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [?] a -> a
    [?] b -> b
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Dependencyes can be skipped using `skip_deps=True`.

    >>> print_merge(init_run_merge(run, empty_dir, skip_deps=True))
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    To skip:
    [?] a -> a
    [?] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [?] subdir/c -> subdir/c
    [d] yyy -> ?
    [d] zzz -> ?

Skip both dependencies and source code:

    >>> print_merge(init_run_merge(run, empty_dir, skip_deps=True, skip_sourcecode=True))
    To copy:
    To skip:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [?] a -> a
    [?] b -> b
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    [?] subdir/c -> subdir/c
    [d] yyy -> ?
    [d] zzz -> ?

Files can be excluded using patterns in the `exclude` option.

Exclude all files:

    >>> print_merge(init_run_merge(run, empty_dir, exclude=("*",)))
    To copy:
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [x] .guild/sourcecode/op.py -> op.py
    [x] .guild/sourcecode/overlap.py -> overlap.py
    [?] a -> a
    [?] b -> b
    [x] dep-1 -> dep-1
    [x] dep-subdir/dep-2 -> dep-subdir/dep-2
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

If `copy_all=True`, Guild attempts to copy all files including
'other'. These too can be excluded with `exclude`. In this case, the
reason for skipping is `x` (user-excluded).

    >>> print_merge(init_run_merge(run, empty_dir, copy_all=True, exclude=("*",)))
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

    >>> print_merge(init_run_merge(run, empty_dir, exclude=("*.py", "*.yml")))
    To copy:
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [x] .guild/sourcecode/op.py -> op.py
    [x] .guild/sourcecode/overlap.py -> overlap.py
    [?] a -> a
    [?] b -> b
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

When we attempt to exclude source code files using run paths, the
files don't match.

    >>> print_merge(init_run_merge(run, empty_dir, exclude=(
    ...     ".guild/sourcecode/*.py",
    ...     ".guild/sourcecode/*.yml")
    ... ))
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [?] a -> a
    [?] b -> b
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Other exclude patterns:

    >>> print_merge(init_run_merge(run, empty_dir, exclude=("a", "subdir/*")))
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [?] a -> a
    [?] b -> b
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

    >>> print_merge(init_run_merge(run, empty_dir, copy_all=True, exclude=("a", "subdir/*")))
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

    >>> print_merge(init_run_merge(run, empty_dir, exclude=("guild.yml", "dep-*")))
    To copy:
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    To skip:
    [x] .guild/sourcecode/guild.yml -> guild.yml
    [?] a -> a
    [?] b -> b
    [x] dep-1 -> dep-1
    [x] dep-subdir/dep-2 -> dep-subdir/dep-2
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

    >>> print_merge(init_run_merge(run, empty_dir, copy_all=True, exclude=("guild.yml", "dep-*")))
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

### Merging to a non-empty directory

So far the tests show files-to-copy when merging to an empty
directory. When Guild merges to a non-empty directory, it compares
files to copy with existing files. Exiting files that are the same as
the corresponding run file are skipped with the reason code 'u',
indicating *unchanged*.

Create a new target directory.

    >>> target_dir = mkdtemp()

Here are the default merge files for the empty directory:

    >>> default_merge = init_run_merge(run, target_dir)
    >>> print_merge(default_merge)
    To copy:
    [s] .guild/sourcecode/guild.yml -> guild.yml
    [s] .guild/sourcecode/op.py -> op.py
    [s] .guild/sourcecode/overlap.py -> overlap.py
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [?] a -> a
    [?] b -> b
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Copy all of the default files by applying the merge (tests for this
function are below). We use a logger to print what we copy.

    >>> from guild.run_merge import apply_run_merge

    >>> def copy_logger(_merge, copy_file, _src, _dest):
    ...     print(f"Copying {copy_file.run_path}")

    >>> apply_run_merge(default_merge, copy_logger)
    Copying dep-1
    Copying dep-subdir/dep-2
    Copying .guild/sourcecode/guild.yml
    Copying .guild/sourcecode/op.py
    Copying .guild/sourcecode/overlap.py

The files in the target directory:

    >>> find(target_dir)
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py

Refresh the files in the default merge using `refresh_files()` and
print them.

    >>> default_merge = init_run_merge(run, target_dir)
    >>> print_merge(default_merge)
    To copy:
    To skip:
    [u] .guild/sourcecode/guild.yml -> guild.yml
    [u] .guild/sourcecode/op.py -> op.py
    [u] .guild/sourcecode/overlap.py -> overlap.py
    [?] a -> a
    [?] b -> b
    [u] dep-1 -> dep-1
    [u] dep-subdir/dep-2 -> dep-subdir/dep-2
    [?] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Generated files 'a', 'b', and 'subdir/c' are skipped because they are
classified as 'other', which are skipped by default. We can copy them
by specifying `copy_all=True`.

    >>> copy_all_merge = init_run_merge(run, target_dir, copy_all=True)
    >>> print_merge(copy_all_merge)
    To copy:
    [o] a -> a
    [o] b -> b
    [o] subdir/c -> subdir/c
    To skip:
    [u] .guild/sourcecode/guild.yml -> guild.yml
    [u] .guild/sourcecode/op.py -> op.py
    [u] .guild/sourcecode/overlap.py -> overlap.py
    [u] dep-1 -> dep-1
    [u] dep-subdir/dep-2 -> dep-subdir/dep-2
    [npd] yyy -> ?
    [npd] zzz -> ?

Apply the merge to copy these files.

    >>> apply_run_merge(copy_all_merge, copy_logger)
    Copying a
    Copying b
    Copying subdir/c

    >>> find(target_dir)
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py
    subdir/c

Now that the files exit in the target directory, they're skipped as well.

    >>> copy_all_merge = init_run_merge(run, target_dir, copy_all=True)
    >>> print_merge(copy_all_merge)
    To copy:
    To skip:
    [u] .guild/sourcecode/guild.yml -> guild.yml
    [u] .guild/sourcecode/op.py -> op.py
    [u] .guild/sourcecode/overlap.py -> overlap.py
    [u] a -> a
    [u] b -> b
    [u] dep-1 -> dep-1
    [u] dep-subdir/dep-2 -> dep-subdir/dep-2
    [u] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

If we change any of the files in the target directory, Guild notes
that they're changed and does not skip them (provided they're selected
for copy based on the selection criteria).

Change the contents of some of the target directory files.

    >>> write(path(target_dir, "a"), "aaa")
    >>> write(path(target_dir, "dep-1"), "ddd")
    >>> write(path(target_dir, "dep-subdir", "dep-2"), "dddd")
    >>> write(path(target_dir, "op.py"), "ooo")

Refresh the copy-all merge and print the merge files.

    >>> copy_all_merge = init_run_merge(run, target_dir, copy_all=True)
    >>> print_merge(copy_all_merge)
    To copy:
    [s] .guild/sourcecode/op.py -> op.py
    [o] a -> a
    [d] dep-1 -> dep-1
    [d] dep-subdir/dep-2 -> dep-subdir/dep-2
    To skip:
    [u] .guild/sourcecode/guild.yml -> guild.yml
    [u] .guild/sourcecode/overlap.py -> overlap.py
    [u] b -> b
    [u] subdir/c -> subdir/c
    [npd] yyy -> ?
    [npd] zzz -> ?

Apply the merge again - this copies the changed files to the target
directory.

    >>> apply_run_merge(copy_all_merge)

Compare the run directory with the target directory. Use links to dirs
to clarify report output.

    >>> compare_dirs((run.dir, "run-dir"), (target_dir, "target-dir"))
    diff /run-dir /target-dir
    Only in /run-dir : ['.guild', 'yyy', 'zzz']
    Only in /target-dir : ['guild.yml', 'op.py', 'overlap.py']
    Identical files : ['a', 'b', 'dep-1']
    Common subdirectories : ['dep-subdir', 'subdir']
    <BLANKLINE>
    diff /run-dir/dep-subdir /target-dir/dep-subdir
    Identical files : ['dep-2']
    <BLANKLINE>
    diff /run-dir/subdir /target-dir/subdir
    Identical files : ['c']

## Applying a merge

To apply a merge - i.e. copy the designated files to a target
directory - use `run_merge.appyly_run_merge`.

Merges are applied to a target directory.

As noted earlier, Guild copies source code and project local
dependencies by default.

    >>> target_dir = mkdtemp()
    >>> apply_run_merge(init_run_merge(run, target_dir))
    >>> find(target_dir)
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py

Compare the original project directory with the target directory.

    >>> compare_dirs((sample, "sample"), (target_dir, "target-dir"))
    diff /sample /target-dir
    Only in /sample : ['.gitignore', 'a', 'b', 'files.zip', 'subdir']
    Identical files : ['dep-1', 'guild.yml', 'op.py', 'overlap.py']
    Common subdirectories : ['dep-subdir']
    <BLANKLINE>
    diff /sample/dep-subdir /target-dir/dep-subdir
    Identical files : ['dep-2']

We can copy all files, included run-generated files, by specifying
`copy_all=True`.

    >>> target_dir = mkdtemp()
    >>> apply_run_merge(init_run_merge(run, target_dir, copy_all=True))
    >>> find(target_dir)
    a
    b
    dep-1
    dep-subdir/dep-2
    guild.yml
    op.py
    overlap.py
    subdir/c

    >>> compare_dirs((sample, "sample"), (target_dir, "target-dir"))
    diff /sample /target-dir
    Only in /sample : ['.gitignore', 'files.zip']
    Identical files : ['a', 'b', 'dep-1', 'guild.yml', 'op.py', 'overlap.py']
    Common subdirectories : ['dep-subdir', 'subdir']
    <BLANKLINE>
    diff /sample/dep-subdir /target-dir/dep-subdir
    Identical files : ['dep-2']
    <BLANKLINE>
    diff /sample/subdir /target-dir/subdir
    Identical files : ['c']

Copy only source code files by skipping dependencies.

    >>> target_dir = mkdtemp()
    >>> apply_run_merge(init_run_merge(run, target_dir, skip_deps=True))
    >>> find(target_dir)
    guild.yml
    op.py
    overlap.py

    >>> compare_dirs((sample, "sample"), (target_dir, "target-dir"))
    diff /sample /target-dir
    Only in /sample : ['.gitignore', 'a', 'b', 'dep-1', 'dep-subdir', 'files.zip', 'subdir']
    Identical files : ['guild.yml', 'op.py', 'overlap.py']

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

    >>> from guild.run_merge import _prune_overlapping_targets

Helper to test pruning.

    >>> def prune(files, prefer_nonsource=False):
    ...     from guild.run_merge import RunMerge, CopyFile
    ...     to_copy = [
    ...         CopyFile(file_type, None, target_path)
    ...         for file_type, target_path in files
    ...     ]
    ...     merge = RunMerge(
    ...         run=None,
    ...         target_dir=None,
    ...         copy_all=False,
    ...         skip_sourcecode=False,
    ...         skip_deps=False,
    ...         exclude=None,
    ...         to_copy=to_copy,
    ...         to_skip=[]
    ...     )
    ...     _prune_overlapping_targets(merge, prefer_nonsource)
    ...     return [(cf.file_type, cf.target_path) for cf in merge.to_copy]

Empty case:

    >>> prune([])
    []

Non overlapping:

    >>> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt")
    ... ])
    [('s', 'foo.txt'), ('d', 'bar.txt')]

    >>> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt")
    ... ],
    ... prefer_nonsource=True)
    [('s', 'foo.txt'), ('d', 'bar.txt')]

Overlapping source code and dependency:

    >>> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "foo.txt")
    ... ])
    [('s', 'foo.txt')]

    >>> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "foo.txt")
    ... ],
    ... prefer_nonsource=True)
    [('d', 'foo.txt')]

Overlapping source code and generated:

    >>> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt"),
    ...     ("g", "foo.txt")
    ... ])
    [('s', 'foo.txt'), ('d', 'bar.txt')]

    >>> prune([
    ...     ("s", "foo.txt"),
    ...     ("d", "bar.txt"),
    ...     ("g", "foo.txt")
    ... ],
    ... prefer_nonsource=True)
    [('d', 'bar.txt'), ('g', 'foo.txt')]

## Unknown manifest file type

When consulting the run manifest, Guild handles two file types: source
code (indicated by an 's' type) and a dependency (indicated by a 'd'
type).

When Guild reads an entry from a manifest that has an unknown type,
it includes the file in `merge.to_skip` with a type code of '?'.

When Guild reads an entry from a manifest has an unexpected number of
parts, it logs an error message and omits the file from
`merge.to_skip`.

To illustrate, we need a run with a manifest that contains invalid
entries. We create one entry with too few parts to split and another
entry with an usupported file type.

    >>> from guild.manifest import Manifest
    >>> from guild.run import for_dir as run_for_dir

    >>> run_dir = mkdtemp()
    >>> mkdir(path(run_dir, ".guild"))
    >>> touch(path(run_dir, "barfoo"))

    >>> with Manifest(path(run_dir, ".guild", "manifest"), "w") as m:
    ...     m.write(["z", "foobar"])  # too few parts to split
    ...     m.write(["z", "barfoo", "xxx", "file:barfoo"])  # unknown type

    >>> with LogCapture() as log:
    ...     print_merge(init_run_merge(run_for_dir(run_dir), mkdtemp()))
    To copy:
    To skip:
    [?] barfoo -> file:barfoo

    >>> log.print_all()
    WARNING: unexpected manfiest entry for run ...: ['z', 'foobar']
    WARNING: unknown manifest file type 'z' for run file 'barfoo'
