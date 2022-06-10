# Link vs Copy Dependencies

As of 0.7, Guild supports copying resources as well as links. As of
Guild 0.8.2, the default behavior is to copy dependencies. Prior to
this version, the default behavior is to link.

Delete runs for these tests.

    >>> quiet("guild runs rm -y")

Here's a project that demonstrates various resources.

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "guild.yml"), """
    ... op-1:
    ...   main: guild.pass
    ...   requires:
    ...     - file: a.txt
    ...       name: copy-default
    ...       rename: a copy-default
    ...     - file: a.txt
    ...       name: link-explicit
    ...       target-type: link
    ...       rename: a link-explicit
    ...     - file: a.txt
    ...       name: copy-explicit
    ...       target-type: copy
    ...       rename: a copy-explicit
    ...
    ... op-2:
    ...   main: guild.pass
    ...   requires:
    ...    - file: files
    ...      target-type: link
    ...      rename: files files-link
    ...      name: link
    ...    - file: files
    ...      rename: files files-copy
    ...      name: copy
    ... """)

    >>> write(path(project_dir, "a.txt"), "Hello")

Create a nested list of subdirectories with a file:

    >>> cur = path(project_dir, "files")
    >>> mkdir(cur)
    >>> for _ in range(10):
    ...     cur = path(cur, "a")
    ...     mkdir(cur)
    >>> write(path(cur, "a.txt"), "Hello, deeply")

    >>> cd(project_dir)

Run `op-1`:

    >>> run("guild run op-1 -y")
    Resolving copy-default dependency
    Resolving link-explicit dependency
    Resolving copy-explicit dependency
    <exit 0>

    >>> run("guild ls")
    ???:
      copy-default.txt
      copy-explicit.txt
      link-explicit.txt
    <exit 0>

Here's the contents of each file:

    >>> run("guild cat -p copy-default.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p copy-explicit.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p link-explicit.txt")
    Hello
    <exit 0>

We can test the linkedness of each file by modifying the project
source `a.txt`. This highlights the problem with linking: changes to a
project source implicitly change runs.

    >>> write(path(project_dir, "a.txt"), "Hola")

Here are the three run files again:

    >>> run("guild cat -p copy-default.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p copy-explicit.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p link-explicit.txt")
    Hola
    <exit 0>

Run op-1:

    >>> run("guild run op-2 -y")
    Resolving link dependency
    Resolving copy dependency
    <exit 0>

The files:

    >>> run("guild ls")
    ???:
      files-copy/
      files-copy/a/
      files-copy/a/a/
      files-copy/a/a/a/
      files-copy/a/a/a/a/
      files-copy/a/a/a/a/a/
      files-copy/a/a/a/a/a/a/
      files-copy/a/a/a/a/a/a/a/
      files-copy/a/a/a/a/a/a/a/a/
      files-copy/a/a/a/a/a/a/a/a/a/
      files-copy/a/a/a/a/a/a/a/a/a/a/
      files-copy/a/a/a/a/a/a/a/a/a/a/a.txt
      files-link/
    <exit 0>

The resolved files:

    >>> run("guild cat -p files-copy/a/a/a/a/a/a/a/a/a/a/a.txt")
    Hello, deeply
    <exit 0>

    >>> run("guild cat -p files-link/a/a/a/a/a/a/a/a/a/a/a.txt")
    Hello, deeply
    <exit 0>

Delete the `files` directory from the project.

    >>> rmdir(path(project_dir, "files"))

The remaining files don't include `files`:

    >>> find(project_dir)
    a.txt
    guild.yml

The resolved file copy is still available.

    >>> run("guild cat -p files-copy/a/a/a/a/a/a/a/a/a/a/a.txt")
    Hello, deeply
    <exit 0>

The linked file is not available.

    >>> run("guild cat -p files-link/a/a/a/a/a/a/a/a/a/a/a.txt")
    guild: .../files-link/a/a/a/a/a/a/a/a/a/a/a.txt does not exist
    <exit 1>
