# Remote comment hello

Confirm current latest run.

    >>> run("guild runs -r guild-uat -n1")
    [1:...]  gpkg.hello/hello-op  ...  completed  remote-run-123
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
    <exit 0>

Add a comment.

    >>> run("guild comment -a 'A nice comment.' -r guild-uat -y")
    Added comment to 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
    [1] ... ...-...-... ...:...:...
    <BLANKLINE>
      A nice comment.
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
      -
        body: A nice comment.
        host: ...
        time: ...
        user: ...
    <exit 0>

Add another comment.

    >>> run("guild comment -a 'A second comment.' -r guild-uat -y")
    Added comment to 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
    [1] ...
    <BLANKLINE>
      A nice comment.
    <BLANKLINE>
    [2] ...
    <BLANKLINE>
      A second comment.
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
      -
        body: A nice comment.
        host: ...
        time: ...
        user: ...
      -
        body: A second comment.
        host: ...
        time: ...
        user: ...
    <exit 0>

Filter runs by comment.

    >>> run("guild runs -Fc nice -r guild-uat")
    [1:...]  gpkg.hello/hello-op  ...  completed  remote-run-123
    <exit 0>

    >>> run("guild runs -Fc second -r guild-uat")
    [1:...]  gpkg.hello/hello-op  ...  completed  remote-run-123
    <exit 0>

    >>> run("guild runs -Fc 'no match' -r guild-uat")
    <exit 0>

Delete the first comment.

    >>> run("guild comment --delete 1 -r guild-uat -y")
    Deleted comment for 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
    [1] ...
    <BLANKLINE>
      A second comment.
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
      -
        body: A second comment.
        host: ...
        time: ...
        user: ...
    <exit 0>

Clear all comments.

    >>> run("guild comment --clear -r guild-uat -y")
    Deleted all comments for 1 run(s)
    <exit 0>

    >>> run("guild comment --list -r guild-uat")
    ???  gpkg.hello/hello-op  ...  completed  remote-run-123
      <no comments>
    <exit 0>

    >>> run("guild runs info --comments -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    comments:
    <exit 0>
