# Guild example: hello

    >>> cd(example("hello"))

List operations:

    >>> run("guild ops")
    hello       Say hello to my friends
    hello-file  Show a message from a file
    hello-op    Show a message from a hello-file operation
    <exit 0>

## `hello`

    >>> run("guild run hello -y")
    Hello Guild!
    <exit 0>

    >>> run("guild run hello msg=Whoop -y")
    Whoop
    <exit 0>


## `hello-file`

    >>> run("guild run hello-file -y")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

    >>> tmp = mkdtemp()
    >>> tmp_file = path(tmp, "hello")
    >>> write(tmp_file, "A temp file!")

    >>> run("guild run hello-file file=%s -y" % tmp_file)
    Resolving file dependency
    Using .../hello for file resource
    Reading message from .../hello
    A temp file!
    Saving message to msg.out
    <exit 0>

## `hello-op`

    >>> run("guild run hello-op -y")
    Resolving op dependency
    Using run ... for op resource
    Reading message from msg.out
    A temp file!
    <exit 0>

    >>> run("guild run hello-op op=`guild select -Fo hello-file 2` -y")
    Resolving op dependency
    Using run ... for op resource
    Reading message from msg.out
    Hello, from a file!
    <exit 0>
