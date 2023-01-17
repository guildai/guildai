# Run manifest

A run manifest is a [Guild manifest](manifest.md) that records each of
the files copied to the run directory in preparation for the
operation.

Run manifests record source files and resolved resource files.

We use the `get-started` project for these tests.

## Source code files

Manifests contain a list of all source code files copied.

Generate a run of `train.py` from the `get-started` project.

    >>> use_project("get-started")

    >>> run("guild run train.py -y")
    x: 0.100000
    noise: 0.100000
    loss: ...

The run manifest:

    >>> run("guild cat -p .guild/manifest")
    s TEST.md a5a7f25a2e67c92644dc4f24b37b14e997c177e8 TEST.md
    s train.py 32001b882e707290cc988043abb9b99ddee94c25 train.py

Each line conists of an entry type followed by entry arguments The two
entries are for source code (`s` type). The arguments are:

- run dir relative path
- file sha1 digest
- project relative path

## Resolved dependency sources

Manifests also contain resolved dependencies.

Generate a `file-deps` run from the `run-manifest` project.

    >>> use_project("run-manifest")

    >>> run("guild run file-deps -y")
    Resolving file:file1.txt
    Resolving file:file2.txt
    Resolving file:files.zip
    Unpacking .../samples/projects/run-manifest/files.zip

The manifest contains source code files and resolved dependencies.

    >>> run("guild cat -p .guild/manifest")
    s guild.yml dfa0dbc1c7eadf4270fd755188137a0c17e841d6 guild.yml
    s subdir/eee da39a3ee5e6b4b0d3255bfef95601890afd80709 subdir/eee
    s subdir/fff da39a3ee5e6b4b0d3255bfef95601890afd80709 subdir/fff
    d file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:file1.txt
    d file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:file2.txt
    d zip/file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:files.zip file1.txt
    d zip/file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:files.zip file2.txt

The consistent `sha1` digests reflect that the samples files are all empty.

    >>> import hashlib

    >>> hashlib.sha1(b"").hexdigest()
    'da39a3ee5e6b4b0d3255bfef95601890afd80709'

## Support functions

Functions for working with run manifests are defined in `guild.run_manifest`.

    >>> from guild import run_manifest

### Reading manifest entries

The function `read_manifest_entries` returns a list of entries for a
run manifest.

    >>> last_run_dir = run_capture("guild select --dir")
    >>> pprint(run_manifest.read_manifest_entries(last_run_dir))
    [['s', 'guild.yml', 'dfa0dbc1c7eadf4270fd755188137a0c17e841d6', 'guild.yml'],
     ['s', 'subdir/eee', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'subdir/eee'],
     ['s', 'subdir/fff', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'subdir/fff'],
     ['d',
      'file1.txt',
      'da39a3ee5e6b4b0d3255bfef95601890afd80709',
      'file:file1.txt'],
     ['d',
      'file2.txt',
      'da39a3ee5e6b4b0d3255bfef95601890afd80709',
      'file:file2.txt'],
     ['d',
      'zip/file1.txt',
      'da39a3ee5e6b4b0d3255bfef95601890afd80709',
      'file:files.zip',
      'file1.txt'],
     ['d',
      'zip/file2.txt',
      'da39a3ee5e6b4b0d3255bfef95601890afd80709',
      'file:files.zip',
      'file2.txt']]

### Iterating run files

The function `iter_run_files` returns an iterator that returns tuples
of filename and corresponding manifest. If a run file doesn't
correspond with a manifest entry, the second element is None.

Show all the files for the run.

    >>> run("guild ls --all -n")
    .guild/
    .guild/attrs/
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/env
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/manifest
    .guild/opref
    .guild/output
    .guild/output.index
    file1.txt
    file2.txt
    guild.yml
    subdir/
    subdir/eee
    subdir/fff
    zip/
    zip/file1.txt
    zip/file2.txt

Create a function that prints iterated run files.

    >>> def print_run_files(run_dir, followlinks=False):
    ...     for path, args in sorted(
    ...         run_manifest.iter_run_files(run_dir, followlinks)
    ...     ):
    ...         print(path, args)

Print the files for the last run.

    >>> print_run_files(last_run_dir)  # doctest: +REPORT_UDIFF
    file1.txt ['d', 'file1.txt', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'file:file1.txt']
    file2.txt ['d', 'file2.txt', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'file:file2.txt']
    guild.yml ['s', 'guild.yml', 'dfa0dbc1c7eadf4270fd755188137a0c17e841d6', 'guild.yml']
    subdir/eee ['s', 'subdir/eee', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'subdir/eee']
    subdir/fff ['s', 'subdir/fff', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'subdir/fff']
    zip/file1.txt ['d', 'zip/file1.txt', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'file:files.zip', 'file1.txt']
    zip/file2.txt ['d', 'zip/file2.txt', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'file:files.zip', 'file2.txt']

#### Directory entries

When a manifest entry path is a directory, any run files under that
directory are associated with the directory entry args in
`iter_run_files`.

Create a sample run with a directory structure containing
subdirectories and symbolic links to other directories.

    >>> run_dir = mkdtemp()
    >>> mkdir(path(run_dir, ".guild"))
    >>> touch(path(run_dir, ".guild", "output"))
    >>> mkdir(path(run_dir, ".guild", "attrs"))
    >>> touch(path(run_dir, ".guild", "attrs", "id"))
    >>> touch(path(run_dir, "dep-1"))
    >>> touch(path(run_dir, "dep-2"))
    >>> touch(path(run_dir, "src-1"))
    >>> touch(path(run_dir, "src-2"))
    >>> mkdir(path(run_dir, "subdir-1"))
    >>> touch(path(run_dir, "subdir-1", "interim-1"))
    >>> touch(path(run_dir, "subdir-1", "interim-2"))
    >>> mkdir(path(run_dir, "subdir-1", "subdir-2"))
    >>> touch(path(run_dir, "subdir-1", "subdir-2", "interim-3"))
    >>> touch(path(run_dir, "subdir-1", "subdir-2", "interim-4"))
    >>> touch(path(run_dir, "subdir-1", "subdir-2", "dep-3"))
    >>> link_target = mkdtemp()
    >>> touch(path(link_target, "dep-4"))
    >>> mkdir(path(link_target, "subdir-3"))
    >>> touch(path(link_target, "subdir-3", "dep-5"))
    >>> symlink(link_target, path(run_dir, "linked-subdir-1"))

List the files for the run dir.

    >>> find(run_dir, followlinks=True)  # doctest: +REPORT_UDIFF
    .guild/attrs/id
    .guild/output
    dep-1
    dep-2
    linked-subdir-1
    linked-subdir-1/dep-4
    linked-subdir-1/subdir-3/dep-5
    src-1
    src-2
    subdir-1/interim-1
    subdir-1/interim-2
    subdir-1/subdir-2/dep-3
    subdir-1/subdir-2/interim-3
    subdir-1/subdir-2/interim-4

Generate a manifest for the run.

    >>> m = run_manifest.manifest_for_run(run_dir, "w")
    >>> m.write(["d", "dep-1"])
    >>> m.write(["d", "dep-2"])
    >>> m.write(["s", "src-1"])
    >>> m.write(["s", "src-2"])
    >>> m.write(["i", "subdir-1"])
    >>> m.write(["d", "subdir-1/subdir-2/dep-3"])
    >>> m.write(["d", "linked-subdir-1"])
    >>> m.close()

As the run directory uses a symbolic link (simulating a link to a
resolved dependency) we get a different listing depending on whether
or not we specify `followlinks`.

    >>> print_run_files(run_dir, followlinks=False)  # doctest: +REPORT_UDIFF
    dep-1 ['d', 'dep-1']
    dep-2 ['d', 'dep-2']
    linked-subdir-1 ['d', 'linked-subdir-1']
    src-1 ['s', 'src-1']
    src-2 ['s', 'src-2']
    subdir-1 ['i', 'subdir-1']
    subdir-1/interim-1 ['i', 'subdir-1']
    subdir-1/interim-2 ['i', 'subdir-1']
    subdir-1/subdir-2/dep-3 ['d', 'subdir-1/subdir-2/dep-3']
    subdir-1/subdir-2/interim-3 ['i', 'subdir-1']
    subdir-1/subdir-2/interim-4 ['i', 'subdir-1']

    >>> print_run_files(run_dir, followlinks=True)  # doctest: +REPORT_UDIFF
    dep-1 ['d', 'dep-1']
    dep-2 ['d', 'dep-2']
    linked-subdir-1 ['d', 'linked-subdir-1']
    linked-subdir-1/dep-4 ['d', 'linked-subdir-1']
    linked-subdir-1/subdir-3/dep-5 ['d', 'linked-subdir-1']
    src-1 ['s', 'src-1']
    src-2 ['s', 'src-2']
    subdir-1 ['i', 'subdir-1']
    subdir-1/interim-1 ['i', 'subdir-1']
    subdir-1/interim-2 ['i', 'subdir-1']
    subdir-1/subdir-2/dep-3 ['d', 'subdir-1/subdir-2/dep-3']
    subdir-1/subdir-2/interim-3 ['i', 'subdir-1']
    subdir-1/subdir-2/interim-4 ['i', 'subdir-1']
