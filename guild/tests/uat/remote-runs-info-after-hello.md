# Runs info

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    from: gpkg.hello==0.1
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: op=...
    sourcecode_digest: ...
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main hello.cat --
    exit_status: 0
    pid:
    tags:
    flags:
      op: ...
    scalars:
    <exit 0>

With manifest:

    >>> run("guild runs info -m -r guild-uat")
    id: ...
    ...
    manifest:
      dependencies:
        - msg.out
      sourcecode:
        - .guild/sourcecode/README.md
        - .guild/sourcecode/data/hello-2.txt
        - .guild/sourcecode/data/hello.txt
        - .guild/sourcecode/guild.yml
        - .guild/sourcecode/hello/__init__.py
        - .guild/sourcecode/hello/cat.py
        - .guild/sourcecode/hello/say.py
    <exit 0>
