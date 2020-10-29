# Remote tag hello

Confirm current latest run.

    >>> run("guild runs -r guild-uat -n1")
    [1:...]  gpkg.hello/hello-op  ...  completed  remote-run-123
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    tags:
    ...
    <exit 0>

Add two tags with label sync.

    >>> run("guild tag -a blue -a green --sync-labels -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs -r guild-uat -n1")
    [1:...]  gpkg.hello/hello-op  ...  completed  blue green remote-run-123
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: blue green remote-run-123
    ...
    tags:
      - blue
      - green
    ...
    <exit 0>

Delete two tags, one non-existing.

    >>> run("guild tag -d blue -d yellow -s -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: green remote-run-123
    ...
    tags:
      - green
    ...
    <exit 0>

Delete an existing tag, add a new tag.

    >>> run("guild tag -d green -a orange -s -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: orange remote-run-123
    ...
    tags:
      - orange
    ...
    <exit 0>

Clear tags and add a new tag.

    >>> run("guild tag -c -a cyan -s -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: cyan remote-run-123
    ...
    tags:
      - cyan
    ...
    <exit 0>

Clear all tags without label sync.

    >>> run("guild tag -c -r guild-uat -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info -r guild-uat")
    id: ...
    operation: gpkg.hello/hello-op
    ...
    label: cyan remote-run-123
    ...
    tags:
    ...
    <exit 0>

Reset run label (assumed by subsequent remote tests).

    >>> quiet("guild label -s remote-run-123 -r guild-uat -y")
