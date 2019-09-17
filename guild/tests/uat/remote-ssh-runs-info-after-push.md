# Remote runs info

    >>> run("guild runs info --remote guild-uat-ssh")
    id: ...
    operation: hello:from-file
    from: .../examples/hello/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    sourcecode_digest: 0d5131c7879d544cbde683da86c06085
    run_dir: ...
    command: ... -um guild.op_main say -- --file msg.txt
    exit_status: 0
    pid:
    flags:
      file: msg.txt
    scalars:
    <exit 0>
