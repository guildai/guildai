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
    Resolving file:file1.txt
    Resolving file:file2.txt
    Resolving file:files.zip
    Unpacking .../samples/projects/run-manifest/files.zip

    >>> run = project.list_runs()[0]
    >>> cat(run.guild_path("manifest"))
    s .guild/sourcecode/file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file1.txt
    s .guild/sourcecode/file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file2.txt
    s .guild/sourcecode/guild.yml 3b884a437e6606986b1cac978e14e77fd243cba8 guild.yml
    s .guild/sourcecode/subdir/eee da39a3ee5e6b4b0d3255bfef95601890afd80709 subdir/eee
    s .guild/sourcecode/subdir/fff da39a3ee5e6b4b0d3255bfef95601890afd80709 subdir/fff
    d file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:file1.txt
    d file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:file2.txt
    d zip/file1.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:files.zip file1.txt
    d zip/file2.txt da39a3ee5e6b4b0d3255bfef95601890afd80709 file:files.zip file2.txt
    <BLANKLINE>
