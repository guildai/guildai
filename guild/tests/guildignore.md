# guildignore

As of version 0.9, Guild supports files named `.guildignore` in a project root
directory. This file contains entries patterns that Guild should ignore when
copying source code. The file conforms with the
[gitignore](https://git-scm.com/docs/gitignore) specification.

The `hello-legacy` sample project uses a `.guildignore` file to exclude a file
from source code copy. The project is considered "legacy" because Guild 0.9 and
later copies source code files to the run root, which ends up copying a
required file (see the `hello` project for the current implementation).

    >>> cd(sample("projects", "hello-legacy"))

We run various operations in the project to illustrate how `.guildignore` is
used.  We use a new Guild home to isolate runs for this test.

    >>> set_guild_home(mkdtemp())

Files in the `hello-legacy` project:

    >>> pprint(dir())
    ['.guildignore',
     'README.md',
     'cat.py',
     'data',
     'guild.yml',
     'hello.txt',
     'repeat.py',
     'say.py']

Note that `hello.txt` exists in the project.

`.guildignore` contains two entries to ignore.

    >>> cat(".guildignore")
    hello.txt
    data

This tells Guild not to copy `hello.txt` and anything in the subdirectory
`data` to the run directory as source code.

Let's the `hello` operation. This simply prints a message and doesn't require a
file.

    >>> run("guild run hello -y")
    Hello Guild!
    <exit 0>

We see that neither `hello.txt` nor any files under `data` are copied to the run
directory for this operation.

    >>> run("guild ls -n")
    README.md
    cat.py
    guild.yml
    repeat.py
    say.py
    <exit 0>

The `hello-file` operation requires `hello.txt`.

    >>> run("guild run hello-file -y")
    Resolving file
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

The file `hello.txt` was copied to the run directory in this case because it's
listed as an explicit dependeny in [guild.yml](guild.yml) for the `hello-file`
operation.

    >>> run("guild ls -n")
    README.md
    cat.py
    guild.yml
    hello.txt
    msg.out
    repeat.py
    say.py
    <exit 0>
