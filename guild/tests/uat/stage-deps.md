---
# Missing 'file: unspecified' in run preview - what happened to this?

doctest: +FIXME
---

# Stage deps

Delete runs as baseline.

    >>> quiet("guild runs rm -y")

Use `dependencies` example.

    >>> cd(example("dependencies"))

Warning when missing required op:

    >>> run("guild run file-op", timeout=5)
    WARNING: cannot find a suitable run for required resource 'operation:file'
    You are about to run file-op
      file: unspecified
    Continue? (Y/n)
    <exit ...>

Stage a required op.

    >>> run("guild run file --stage -y")
    Resolving file:file.txt
    file staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

When running, staged runs are selected.

    >>> run("guild run file-op", timeout=5)
    You are about to run file-op
      operation:file: ...
    Continue? (Y/n)
    <exit ...>

Stage downstream op.

    >>> run("guild run file-op --stage", timeout=5)
    You are about to stage file-op
      operation:file: ...
    Continue? (Y/n)
    <exit ...>

When we don't preview the operation or otherwise specify a run for
`file`, the operation staging is skipped.

    >>> run("guild run file-op --stage --yes")
    Resolving operation:file
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
    Resolving file:file.txt
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
    Resolving operation:file
    Using run ... for operation:file
    <exit 0>
