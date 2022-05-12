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
