# Stage deps

Delete runs as baseline.

    >>> quiet("guild runs rm -y")

Use `dependencies` example.

    >>> cd(example("dependencies"))

Warning when missing required op:

    >>> run("guild run file-op", timeout=2)
    WARNING: cannot find a suitable run for required resource 'file'
    You are about to run file-op
      file: unspecified
    Continue? (Y/n)
    <exit ...>

Stage a required op.

    >>> run("guild run file --stage -y")
    Resolving file:file.txt dependency
    file staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

When running, staged runs are selected.

    >>> run("guild run file-op", timeout=2)
    You are about to run file-op
      file: ...
    Continue? (Y/n)
    <exit -9>

Stage downstream op.

    >>> run("guild run file-op --stage", timeout=2)
    You are about to stage file-op
      file: ...
    Continue? (Y/n)
    <exit ...>

When we don't preview the operation or otherwise specify a run for
`file`, the operation staging is skipped.

    >>> run("guild run file-op --stage --yes")
    Resolving file dependency
    Skipping resolution of operation:file because it's being staged
    file-op staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Start staged upstream op.

    >>> upstream = gapi.runs_list()[1]

    >>> upstream.opref.to_opspec()
    'file'

    >>> upstream.status
    'staged'

    >>> run("guild run --start %s --yes" % upstream.id)
    Resolving file:file.txt dependency
    Skipping resolution of file:file.txt because it's already resolved
    <exit 0>

Note that the file dependency is skipped because it was already
resolved above.

Start staged downstream op.

    >>> downstream = gapi.runs_list()[1]

    >>> downstream.opref.to_opspec()
    'file-op'

    >>> downstream.status
    'staged'

    >>> run("guild run --start %s --yes" % downstream.id)
    Resolving file dependency
    Using run ... for file resource
    <exit 0>
