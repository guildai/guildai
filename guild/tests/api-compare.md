# Guild `api compare` command

Generate some sample runs.

    >>> project = Project(example("hello"))

    >>> project.run("hello-file")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out

    >>> project.run("hello", flags={"msg": "Yo yo yo"})
    Yo yo yo

Show compare data for runs:

    >>> run(
    ...     f"guild -H {project.guild_home} api compare -f",
    ...     cwd=project.cwd)  # doctest: +REPORT_UDIFF
    [
      [
        "id",
        "operation",
        "started",
        "time",
        "status",
        "label",
        "msg",
        "file"
      ],
      [
        "...",
        "hello",
        "...",
        "...",
        "completed",
        "msg='Yo yo yo'",
        "Yo yo yo",
        null
      ],
      [
        "...",
        "hello-file",
        "...",
        "...",
        "completed",
        "file=hello.txt",
        null,
        "hello.txt"
      ]
    ]
    <exit 0>
