# Tags

Use the hello example to illustrate tag support.

    >>> cd(example("hello"))

    >>> quiet("guild runs rm -y")

New runs can be tagged using -t:

    >>> quiet("guild run hello -t blue -y")

Tags for a run appear for runs info:

    >>> run("guild runs info")
    id: ...
    operation: hello
    ...
    label: blue msg='Hello Guild!'
    ...
    tags:
      - blue
    ...
    <exit 0>

Default run labels contain tags:

    >>> run("guild runs")
    [1:...]  hello  ...  completed  blue msg='Hello Guild!'
    <exit 0>

Tags can be used as filters:

    >>> run("guild runs -Ft blue")
    [1:...]  hello  ...  completed  blue msg='Hello Guild!'
    <exit 0>

    >>> run("guild runs -Ft green")
    <exit 0>

When used multiple times, tags expand selected runs:

    >>> run("guild runs -Ft green -Ft blue")
    [1:...]  hello  ...  completed  blue msg='Hello Guild!'
    <exit 0>

Tag filters are available in all run related commands. Delete only
runs tagged with 'blue':

    >>> run("guild runs rm -Ft blue -y")
    Deleted 1 run(s)
    <exit 0>

Run tags can be modified at any time. First, generate a run with
'green' tag:

    >>> quiet("guild run hello -t green -y")

Add two more tags. When adding tags, the --sync-labels option can be
used to synchronize the run label with the new tags.

    >>> run("guild tag -a red -a yellow -s -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: hello
    ...
    label: red yellow green msg='Hello Guild!'
    ...
    tags:
      - green
      - red
      - yellow
    ...
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  red yellow green msg='Hello Guild!'
    <exit 0>

Delete a tag:

    >>> run("guild tag -d red -s -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: hello
    ...
    tags:
      - green
      - yellow
    ...
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  yellow green msg='Hello Guild!'
    <exit 0>

Clear all tags:

    >>> run("guild tag -c -s -y")
    Modified tags for 1 run(s)
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: hello
    ...
    tags:
    ...
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  msg='Hello Guild!'
    <exit 0>

When a label is specified for a run, tags are not included in the
label.

    >>> quiet("guild run hello -t blue -l 'hello run' -y")

    >>> run("guild runs")
    [1:...]  hello  ...  completed  hello run
    [2:...]  hello  ...  completed  msg='Hello Guild!'
    <exit 0>

The tags however are still set.

    >>> run("guild runs info")
    id: ...
    operation: hello
    ...
    tags:
      - blue
    ...
    <exit 0>

Add a new tag to all runs:

    >>> run("guild tag -a example : -s -y")
    Modified tags for 2 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  example hello run
    [2:...]  hello  ...  completed  example msg='Hello Guild!'
    <exit 0>

    >>> run("guild runs info 1")
    id: ...
    operation: hello
    ...
    tags:
      - blue
      - example
    ...
    <exit 0>

    >>> run("guild runs info 2")
    id: ...
    operation: hello
    ...
    tags:
      - example
    ...
    <exit 0>

Repeat the addition of a tag. This is idempotent.

    >>> run("guild tag -a example : -s -y")
    Modified tags for 2 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  example hello run
    [2:...]  hello  ...  completed  example msg='Hello Guild!'
    <exit 0>

    >>> run("guild runs info 1")
    id: ...
    operation: hello
    ...
    tags:
      - blue
      - example
    ...
    <exit 0>

    >>> run("guild runs info 2")
    id: ...
    operation: hello
    ...
    tags:
      - example
    ...
    <exit 0>

When --sync-labels is not specified, the run labels are not updated.

    >>> run("guild tag -d example : -y")
    Modified tags for 2 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  example hello run
    [2:...]  hello  ...  completed  example msg='Hello Guild!'
    <exit 0>

The tags, however, are modified.

    >>> run("guild runs info 1")
    id: ...
    operation: hello
    ...
    tags:
      - blue
    ...
    <exit 0>

    >>> run("guild runs info 2")
    id: ...
    operation: hello
    ...
    tags:
    ...
    <exit 0>

When modifying tags without the -y option, Guild shows a clarifying
message related to syncing labels.

    >>> run("guild tag -c", timeout=2)
    You are about to modify tags for the following runs:
    Labels are not updated - use --sync-labels to apply changes run labels.
      [...]  hello  ...  completed  example hello run
    Continue? (Y/n)
    <exit -9>

    >>> run("guild tag -c -s", timeout=2)
    You are about to modify tags for the following runs:
    Labels are updated to reflect the latest tags.
      [...]  hello  ...  completed  example hello run
    Continue? (Y/n)
    <exit -9>
