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
