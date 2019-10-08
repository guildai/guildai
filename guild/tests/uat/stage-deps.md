# Stage deps

Delete runs as baseline.

    >>> quiet("guild runs rm -y")

Use `dependencies` example.

    >>> cd("examples/dependencies")

Warning when missing required op:

    >>> run("guild run requires-file-op", timeout=2)
    WARNING: cannot find a suitable run for required resource 'file'
    You are about to run requires-file-op
    Continue? (Y/n)
    <exit ...>

Stage a required op.

    >>> run("guild run file --stage -y")
    Resolving file:file.txt dependency
    file staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

When running, staged runs aren't selected.

    >>> run("guild run requires-file-op", timeout=2)
    WARNING: cannot find a suitable run for required resource 'file'
    You are about to run requires-file-op
    Continue? (Y/n)
    <exit ...>

Stage downstream op.

    >>> run("guild run requires-file-op --stage", timeout=2)
    You are about to stage requires-file-op
      file: ...
    Continue? (Y/n)
    <exit ...>

    >>> run("guild run requires-file-op --stage --yes")
    Resolving file dependency
    Using output from run ... for file resource
    requires-file-op staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Start staged upstream op.

    >>> upstream = gapi.runs_list()[1]

    >>> upstream.opref.to_opspec()
    'file'

    >>> upstream.status
    'staged'

    >>> run("guild run --start %s --yes" % upstream.id)
    Starting ...
    Resolving file:file.txt dependency
    <exit 0>

Start staged downstream op.

    >>> downstream = gapi.runs_list()[1]

    >>> downstream.opref.to_opspec()
    'requires-file-op'

    >>> downstream.status
    'staged'

    >>> run("guild run --start %s --yes" % downstream.id)
    Starting ...
    Resolving file dependency
    Using output from run ... for file resource
    <exit 0>
