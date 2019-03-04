# Invalid remote

## check

    >>> run("guild check -r invalid-remote-abcd1234")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## label

    >>> run("guild label -r invalid-remote-abcd1234 foobar -y")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## pull

    >>> run("guild pull invalid-remote-abcd1234 -y")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## push

    >>> run("guild push invalid-remote-abcd1234 -y")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## run

    >>> cd("examples/hello")
    >>> run("guild run -y -r invalid-remote-abcd1234 default")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## runs

    >>> run("guild runs -r invalid-remote-abcd1234")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## stop

    >>> run("guild stop -r invalid-remote-abcd1234 -y")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>

## watch

    >>> run("guild watch -r invalid-remote-abcd1234")
    guild: remote 'invalid-remote-abcd1234' is not defined
    Show remotes by running 'guild remotes' or 'guild remotes --help'
    for more information.
    <exit 1>
