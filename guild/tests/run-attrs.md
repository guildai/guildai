# Run attrs

Custom attributes can be defined for an operation using the
`run-attrs` op attr. The `run-attrs` sample project illustrates.

    >>> cd(sample("projects", "run-attrs"))

Guild prohibits use of 'core' attributes.

    >>> run("guild run op -y")  # doctest: +REPORT_UDIFF
    WARNING: Invalid run attribute 'cmd' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'deps' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'env' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'exit_status' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'flags' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'host' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'id' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'initialized' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'label' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'op' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'pip_freeze' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'platform' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'random_seed' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'run_params' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'sourcecode_digest' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'started' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'stopped' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'user' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'user_flags' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'vcs_commit' (reserved attribute) - ignoring
    <exit 0>

Non-core attributes, however, are written.

    >>> run("guild runs info")
    id: ...
    operation: op
    from: .../samples/projects/run-attrs/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    sourcecode_digest: ...
    vcs_commit:
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    another-custom: baz
    custom: bar
    yet-another-custom:
      a: A
      b: 123
      c: 1.234
    tags:
    flags:
    scalars:
    <exit 0>
