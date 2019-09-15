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
    sourcecode_digest: f38982035347da4129fb0f98ef48bb5a
    run_dir: ...
    command: ... -um guild.op_main say -- --file msg.txt
    exit_status: 0
    pid:
    flags:
      file: msg.txt
    <exit 0>
