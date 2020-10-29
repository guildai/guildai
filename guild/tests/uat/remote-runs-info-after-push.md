# Remote runs info

    >>> run("guild runs info --remote guild-uat")
    id: ...
    operation: hello-file
    from: .../hello/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: file=hello.txt
    sourcecode_digest: ...
    vcs_commit: git:...
    run_dir: ...
    command: ... -um guild.op_main cat -- --file hello.txt
    exit_status: 0
    pid:
    tags:
    flags:
      file: hello.txt
    scalars:
    <exit 0>
