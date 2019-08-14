# Remote push hello

This test runs a local hello operation and pushes the run to a remote.

    >>> cd("examples/hello")

Run the op locally:

    >>> run("guild run hello:from-file -y")
    Resolving msg-file dependency
    Hello Guild, from a required file!
    <exit 0>

Push the latest run to the remote:

    >>> run("guild push guild-uat-ssh 1 -y")
    Copying ...
    sending incremental file list
    ...
    <exit 0>

List remote runs:

    >>> run("guild runs -r guild-uat-ssh")
    [1:...]  hello:from-file (.../examples/hello)  ...  completed
    ...
    <exit 0>
