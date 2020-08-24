# Diff

Create a project to generate runs we can diff.

    >>> project = Project(path(mkdtemp(), "diff-project"), GUILD_HOME)
    >>> ensure_dir(project.cwd)
    >>> write(path(project.cwd, "run.py"), "print('hello')")

Run the script twice:

    >>> project.run("run.py")
    hello

    >>> project.run("run.py")
    hello

Show various diff args using `--cmd echo`.

Run directory:

    >>> run("guild diff --cmd echo")
    ???/.guild/runs/.../ .../.guild/runs/.../
    <exit 0>

Source code:

    >>> run("guild diff --sourcecode --cmd echo")
    ???/.guild/runs/.../.guild/sourcecode .../.guild/runs/.../.guild/sourcecode
    <exit 0>

`foo` path:

    >>> run("guild diff --path foo --cmd echo")
    ???/.guild/runs/.../foo .../.guild/runs/.../foo
    <exit 0>

`foo` and `bar` paths:

    >>> run("guild diff --path foo --path bar --cmd echo")
    ???/.guild/runs/.../foo .../.guild/runs/.../foo
    .../.guild/runs/.../bar .../.guild/runs/.../bar
    <exit 0>

Source code to project dir (`--working` option):

    >>> run("guild diff --working --cmd echo")
    ???/.guild/runs/.../.guild/sourcecode .../diff-project
    <exit 0>

Source code to project subdir (`--working-dir` option):

    >>> run("guild diff --working-dir foobar --cmd echo")
    ???/.guild/runs/.../.guild/sourcecode ./foobar
    <exit 0>

Working dir with run 2:

    >>> run("guild diff 2 --working-dir foobar --cmd echo")
    ???/.guild/runs/.../.guild/sourcecode ./foobar
    <exit 0>

Working with runs 1 and 2:

    >>> run("guild diff 1 2 --working --cmd echo")
    guild: cannot specify RUN2 and --working
    <exit 1>

Working dir with runs 1 and 2:

    >>> run("guild diff 1 2 --working-dir foobar --cmd echo")
    guild: cannot specify RUN2 and --working-dir
    <exit 1>

Run a package operation for use with `--working`:

    >>> run("guild run hello:default -y")
    Hello Guild!
    <exit 0>

    >>> run("guild diff --working --cmd echo")
    ???/.guild/sourcecode .../site-packages/gpkg/hello/
    <exit 0>

Create a Guild file in project dir to test diffing with alternative
source code root.

    >>> src_dir = path(project.cwd, "src")
    >>> mkdir(src_dir)
    >>> write(path(src_dir, "run2.py"), "print('hello 2')")

    >>> gf_path = path(project.cwd, "guild.yml")
    >>> write(gf_path, """
    ... run2:
    ...   main: run2
    ...   sourcecode:
    ...     root: src
    ... """)

Run operation:

    >>> project.run("run2")
    hello 2

Diff latest using working:

    >>> run("guild diff --working --cmd echo")
    ???/.guild/sourcecode .../diff-project/src
    <exit 0>

Run a second operation:

    >>> project.run("run2")
    hello 2

Diff a source code path:

    >>> run("guild diff --sourcecode --path run2.py --cmd echo")
    ???/.guild/sourcecode/run2.py .../.guild/sourcecode/run2.py
    <exit 0>

Various errors:

    >>> run("guild diff --working --working-dir foo")
    guild: --working and --working-dir cannot both be specified
    <exit 1>
