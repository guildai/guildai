# Remote push hello

This test runs a local hello operation and pushes the run to a remote.

    >>> cd(example("hello"))

Run the op locally:

    >>> run("guild run hello-file -y")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

Push the latest run to the remote:

    >>> run("guild push guild-uat 1 -y")
    Copying ...
    sending incremental file list
    ...
    <exit 0>

List remote runs:

    >>> run("guild runs -r guild-uat -n 1")
    [1:...]  hello-file (.../hello)  ...  completed  file=hello.txt
    <exit 0>
