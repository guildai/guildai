# slim.resnet prepare flowers

Direct output to /dev/null to avoid freezing (I believe related to
rapid stdout updates from the processing progress).

    >>> run("guild run flowers:prepare -y > /dev/null")
    Resolving slim/lib dependency
    ...
    <exit 0>

List the prepared flowers datasets:

    >>> run("guild runs list flowers")
    [0:...]  slim.datasets/slim-flowers:prepare  ... ...  completed
    <exit 0>
