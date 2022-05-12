# Run manifest

A run manifest is a [Guild manifest](manifest.md) that records each of
the files copied to the run directory in preparation for the
operation.

Run manifests record source files and resolved resource files.

## Source code files

Manifests contain a list of all source code files copied.

    >>> project = Project(sample("projects", "get-started"))
    >>> project.run("train.py")
    x: 0.100000
    noise: 0.100000
    loss: ...

Source code entries are writtn in the form:

    'a ' + run_dir_relative_path + ' ' + sha1 + ' ' + project_dir_relative_path

Show the manifest file contents:

    >>> run = project.list_runs()[0]
    >>> cat(run.guild_path("manifest"))
    s .guild/sourcecode/TEST.md a5a7f25a2e67c92644dc4f24b37b14e997c177e8 TEST.md
    s .guild/sourcecode/train.py 32001b882e707290cc988043abb9b99ddee94c25 train.py
    <BLANKLINE>

## Resolved dependency sources

Manifests also contain resolved dependencies.

    >>> project = Project(sample("projects", "run-manifest"))
    >>> project.run("file-deps")
    Resolving file:file1.txt dependency
    Resolving file:file2.txt dependency
    Resolving file:files.zip dependency
    Unpacking .../samples/projects/run-manifest/files.zip

    >>> run = project.list_runs()[0]
    >>> cat(run.guild_path("manifest"))
    s .guild/sourcecode/file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file1.txt
    s .guild/sourcecode/file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file2.txt
    s .guild/sourcecode/guild.yml fb3e58a20c75a0873f7e2ef42e3085d4fc91ce0b guild.yml
    d file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file1.txt
    d file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file2.txt
    d zip/file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 .../file1.txt
    d zip/file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 .../file2.txt
    <BLANKLINE>

TODO: 'd' entries for unpacked sources (i.e. `zip/file1.txt` and
`zip.file2.txt`) need to refer to the archive parent within the
project - e.g. `files.zip:file1.txt` and `files.zip:file2.txt`. Use a
different entry type if need be. E.g. `pf` for project file or `pa`
for project archive file, etc.
