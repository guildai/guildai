# Comments

Comments can be associated with runs using the `comment` command.

We use the `simple` sample project.

    >>> project = Project(sample("projects", "simple"))

## Specify comment for a run

We can specify a comment when running an operation.

    >>> simple_run, _ = project.run_capture("simple", comment="This is a simple op.")

The comment is included in the run `comments` attribute.

    >>> pprint(simple_run.get("comments"))
    [{'body': 'This is a simple op.',
      'host': '...',
      'time': ...,
      'user': '...'}]

Time is recorded as an epochs timestamp.

    >>> type(simple_run.get("comments")[0]["time"]).__name__
    'int'

## Comments in runs list

The `-c, --comments` option is used to inlude comments in the runs
list.

    >>> run("guild -H '%s' runs -c" % project.guild_home)
    [1:...]  simple (samples/projects/simple)  ...  completed  x=1.0
      ...@... ...-...-... ...:...:...
    <BLANKLINE>
        This is a simple op.
    <exit 0>

## Comments in runs info

The `-c, --comments` option is used to include comments in the runs
into output.

    >>> run("guild -H '%s' runs info --comments" % project.guild_home)
    id: ...
    operation: simple
    ...
    comments:
      -
        body: This is a simple op.
        host: ...
        time: ...-...-... ...:...:...
        user:...
    <exit 0>

## Filtering comments

Runs can be selected using comment filters.

    >>> project.list_runs(comments=["a simple op"])
    [<guild.run.Run '...'>]

    >>> project.list_runs(comments=["not a simple op"])
    []

    >>> project.list_runs(comments=["not simple", "simple"])
    [<guild.run.Run '...'>]

    >>> run("guild -H '%s' runs -Fc 'a simple op'" % project.guild_home)
    [1:...]  simple (samples/projects/simple)  ...  completed  x=1.0
    <exit 0>

    >>> run("guild -H '%s' runs -Fc 'not a simple op'" % project.guild_home)
    <exit 0>

    >>> run("guild -H '%s' cat --output -Fc 'simple op'" % project.guild_home)
    x: 1.0
    y: 2.0
    <exit 0>

    >>> run("guild -H '%s' cat --output -Fc 'complicated'" % project.guild_home)
    guild: no matching runs
    <exit 1>

## Batch and trial comments

Batch comments are specified using the `-bc` option, which is
available for the project API via the `batch_comment` keyword arg.

    >>> project.run("simple",
    ...     flags={"x": [2.0, 3.0]},
    ...     comment="a trial comment",
    ...     batch_comment="my cool batch")
    INFO: [guild] Running trial ...: simple (x=2.0)
    x: 2.0
    y: 3.0
    INFO: [guild] Running trial ...: simple (x=3.0)
    x: 3.0
    y: 4.0

Show comments for the lasts three runs (two trials and one batch).

    >>> run("guild -H '%s' comment -l 1:3" % project.guild_home)
    ???  simple (samples/projects/simple)   ...  completed  x=3.0
    [1] ...
    <BLANKLINE>
      a trial comment
    <BLANKLINE>
    ...  simple (samples/projects/simple)   ...  completed  x=2.0
    [1] ...
    <BLANKLINE>
      a trial comment
    <BLANKLINE>
    ...  simple+ (samples/projects/simple)  ...  completed
    [1] ...
    <BLANKLINE>
      my cool batch
    <exit 0>

## Add comments

Add a comment using the `comment` command with the `-a` option.


    >>> run("guild -H '%s' comment -a 'a second comment' -y" % project.guild_home)
    Added comment to 1 run(s)
    <exit 0>

    >>> run("guild -H '%s' comment --list" % project.guild_home)
    ???  simple (samples/projects/simple)  ...  completed  x=3.0
    [1] ...
    <BLANKLINE>
      a trial comment
    <BLANKLINE>
    [2] ...
    <BLANKLINE>
      a second comment
    <exit 0>

Delete a comment using the `-d` option with the applicable comment index.

    >>> run("guild -H '%s' comment 1 -d 1 -y" % project.guild_home)
    Deleted comment for 1 run(s)
    <exit 0>

    >>> run("guild -H '%s' comment --list" % project.guild_home)
    ???  simple (samples/projects/simple)  ...  completed  x=3.0
    [1] ...
    <BLANKLINE>
      a second comment
    <exit 0>

Clear comments using the `-c` option.

    >>> run("guild -H '%s' comment -c -y" % project.guild_home)
    Deleted all comments for 1 run(s)
    <exit 0>

    >>> run("guild -H '%s' comment --list" % project.guild_home)
    ???  simple (samples/projects/simple)  ...  completed  x=3.0
      <no comments>
    <exit 0>

When adding a comment, `-u` is used to set the user.

    >>> run("guild -H '%s' comment --add 'comment with user' -u harold -y" % project.guild_home)
    Added comment to 1 run(s)
    <exit 0>

A user can include a host in the form `USER@HOST`.

    >>> run("guild -H '%s' comment --add 'comment with user' -u maude@place -y" % project.guild_home)
    Added comment to 1 run(s)
    <exit 0>

    >>> run("guild -H '%s' runs --comments -n1" % project.guild_home)
    [1:...]  simple (samples/projects/simple)   ...  completed  x=3.0
      harold@... ...-...-... ...:...:...
    <BLANKLINE>
        comment with user
    <BLANKLINE>
      maude@place ...-...-... ...:...:...
    <BLANKLINE>
        comment with user
    <BLANKLINE>
    <exit 0>

## Comments run attribute

Comments are saved in the `comments` run attr as YAML formatted plain text.

    >>> run("guild -H '%s' cat -p .guild/attrs/comments" % project.guild_home)
    - body: comment with user
      host: ...
      time: ...
      user: harold
    - body: comment with user
      host: place
      time: ...
      user: maude
    <exit 0>

## Misc

When a batch comment is provided for a non-batch operation, Guild
shows a warning message.

    >>> run("guild -H '%s' run --batch-comment xxx simple -y"
    ...     % project.guild_home, cwd=project.cwd)
    WARNING: operation is not a batch - ignoring batch comment
    x: 1.0
    y: 2.0
    <exit 0>
