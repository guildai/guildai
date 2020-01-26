# Guild example: hello

    >>> cd(example("hello"))

List operations:

    >>> run("guild ops", ignore="Refreshing")
    hello       Say hello to my friends
    hello-file  Shows a message from a file
    hello-op    Show a message from a hello-file operation
    <exit 0>

Run `hello`:

    >>> run("guild run hello -y")
    Hello Guild!
    <exit 0>

    >>> run("guild run hello msg=Whoop -y")
    Whoop
    <exit 0>
