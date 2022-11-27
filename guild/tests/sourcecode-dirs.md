# Source code dirs

As of version 0.9, Guild copies source code to the run root directory
by default. This can be modified by setting the operation
`sourcecode.dest` attribute. The root directory from which source code
is copied can be specified using `sourcecode.root`.

These tests illustrate this behavior using the `sourcecode-dirs`
project.

    >>> cd(sample("projects", "sourcecode-dirs"))

Use a new Guild home to isolate runs.

    >>> set_guild_home(mkdtemp())

The `default` operation copies source code to the run root. Source
code is copied from the project root, which is where the Guild file is
located.

    >>> run("guild run default --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .guild
      exclude dir * containing .guild-nocopy
      exclude dir .git
      exclude .git*, .guildignore
      gitignore + guildignore patterns
    Selected for copy:
      guild.yml
      src/hello
    Skipped:
    <exit 0>

    >>> run("guild run default -y")
    <exit 0>

    >>> run("guild ls -n")
    guild.yml
    src/
    src/hello
    <exit 0>

    >>> run("guild cat -p .guild/attrs/op")
    ???
    sourcecode:
      dest: .
    <exit 0>

The `alt-dest` operation copies source code to the `sourcecode`
subdirectory within the run root.

    >>> run("guild run alt-dest --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from the current directory
    Rules:
      exclude dir .guild
      exclude dir * containing .guild-nocopy
      exclude dir .git
      exclude .git*, .guildignore
      gitignore + guildignore patterns
    Selected for copy:
      guild.yml
      src/hello
    Skipped:
    <exit 0>

    >>> run("guild run alt-dest -y")
    <exit 0>

    >>> run("guild ls -n")
    sourcecode/
    sourcecode/guild.yml
    sourcecode/src/
    sourcecode/src/hello
    <exit 0>

    >>> run("guild cat -p .guild/attrs/op")
    ???
    sourcecode:
      dest: sourcecode
    <exit 0>

`alt-root` copies from the `src` project subdirectory to the run
directory root.

    >>> run("guild run alt-root --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from 'src'
    Rules:
      exclude dir .guild
      exclude dir * containing .guild-nocopy
      exclude dir .git
      exclude .git*, .guildignore
      gitignore + guildignore patterns
    Selected for copy:
      src/hello
    Skipped:
    <exit 0>

    >>> run("guild run alt-root -y")
    <exit 0>

    >>> run("guild ls -n")
    hello
    <exit 0>

    >>> run("guild cat -p .guild/attrs/op")
    ???
    sourcecode:
      dest: .
      root: src
    <exit 0>

`alt-dest-and-root` copies from `src` project subdirectory to the
`sourcecode` run subdirectory.

    >>> run("guild run alt-dest-and-root --test-sourcecode")  # doctest: +REPORT_UDIFF
    Copying from 'src'
    Rules:
      exclude dir .guild
      exclude dir * containing .guild-nocopy
      exclude dir .git
      exclude .git*, .guildignore
      gitignore + guildignore patterns
    Selected for copy:
      src/hello
    Skipped:
    <exit 0>

    >>> run("guild run alt-dest-and-root -y")
    <exit 0>

    >>> run("guild ls -n")
    sourcecode/
    sourcecode/hello
    <exit 0>

    >>> run("guild cat -p .guild/attrs/op")
    ???
    sourcecode:
      dest: sourcecode
      root: src
    <exit 0>
