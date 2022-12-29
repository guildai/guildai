# Link vs Copy Dependencies

As of 0.7, Guild supports copying resources as well as links. As of
Guild 0.8.2, the default behavior is to copy dependencies. Prior to
this version, the default behavior is to link.

Create a project with operations that require various resources.

    >>> project_dir = mkdtemp()

    >>> use_project(project_dir)

    >>> write("guild.yml", """
    ... op-1:
    ...   main: guild.pass
    ...   sourcecode: no
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
    ...   sourcecode: no
    ...   requires:
    ...    - file: files
    ...      target-type: link
    ...      rename: files files-link
    ...      name: linked-files
    ...    - file: files
    ...      rename: files files-copy
    ...      name: copied-files
    ... """)

    >>> write("a.txt", "Hello")

Create a nested list of subdirectories each with a single file.

    >>> cur = "files"
    >>> mkdir(cur)
    >>> write(path(cur, "a.txt"), "Hello files")
    >>> for i in range(5):
    ...     cur = path(cur, "a")
    ...     mkdir(cur)
    ...     write(path(cur, "a.txt"), f"Hello files {i+2}")

List the project files.

    >>> find(".")
    a.txt
    files/a.txt
    files/a/a.txt
    files/a/a/a.txt
    files/a/a/a/a.txt
    files/a/a/a/a/a.txt
    files/a/a/a/a/a/a.txt
    guild.yml

`op-1` required `a.txt` in three variatnts: a default copy, an
explicit link, and an explicit copy.

    >>> run("guild run op-1 -y")
    Resolving copy-default
    Resolving link-explicit
    Resolving copy-explicit
    <exit 0>

    >>> run("guild ls -n")
    copy-default.txt
    copy-explicit.txt
    link-explicit.txt

Verify that the contents of each file is as expected.

    >>> run("guild cat -p copy-default.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p copy-explicit.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p link-explicit.txt")
    Hello
    <exit 0>

We can test the links of each file by modifying the project source
`a.txt`. This highlights the problem with linking: changes to a
project source implicitly change runs.

    >>> write(path(project_dir, "a.txt"), "Hola")

Show the three files - note the linked file has changed, as expected.

    >>> run("guild cat -p copy-default.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p copy-explicit.txt")
    Hello
    <exit 0>

    >>> run("guild cat -p link-explicit.txt")
    Hola
    <exit 0>

`op-2` requires `files` and shows both a link and a copy.

    >>> run("guild run op-2 -y")
    Resolving linked-files
    Resolving copied-files
    <exit 0>

List the run files.

    >>> run("guild ls -n")
    files-copy/
    files-copy/a.txt
    files-copy/a/
    files-copy/a/a.txt
    files-copy/a/a/
    files-copy/a/a/a.txt
    files-copy/a/a/a/
    files-copy/a/a/a/a.txt
    files-copy/a/a/a/a/
    files-copy/a/a/a/a/a.txt
    files-copy/a/a/a/a/a/
    files-copy/a/a/a/a/a/a.txt
    files-link/

Note that `files-link/` is presented as a single directory. This is
because it's a link. We can follow links in the `ls` command by
specifying `-L`.

    >>> run("guild ls -nL")
    files-copy/
    files-copy/a.txt
    files-copy/a/
    files-copy/a/a.txt
    files-copy/a/a/
    files-copy/a/a/a.txt
    files-copy/a/a/a/
    files-copy/a/a/a/a.txt
    files-copy/a/a/a/a/
    files-copy/a/a/a/a/a.txt
    files-copy/a/a/a/a/a/
    files-copy/a/a/a/a/a/a.txt
    files-link/
    files-link/a.txt
    files-link/a/
    files-link/a/a.txt
    files-link/a/a/
    files-link/a/a/a.txt
    files-link/a/a/a/
    files-link/a/a/a/a.txt
    files-link/a/a/a/a/
    files-link/a/a/a/a/a.txt
    files-link/a/a/a/a/a/
    files-link/a/a/a/a/a/a.txt

Show some of the resolved files.

    >>> run("guild cat -p files-copy/a/a/a/a/a.txt")
    Hello files 5
    <exit 0>

    >>> run("guild cat -p files-copy/a/a.txt")
    Hello files 2
    <exit 0>

    >>> run("guild cat -p files-link/a.txt")
    Hello files
    <exit 0>

    >>> run("guild cat -p files-link/a/a/a.txt")
    Hello files 3
    <exit 0>

We can further illustrate the importance of copying required resources
by deleting the project `files` directory.

    >>> rmdir("files")

    >>> find(".")
    a.txt
    guild.yml

The resolved file copy is still available.

    >>> run("guild cat -p files-copy/a/a/a/a/a/a.txt")
    Hello files 6
    <exit 0>

The linked file is not available.

    >>> run("guild cat -p files-link/a/a/a/a/a/a.txt")
    guild: .../files-link/a/a/a/a/a/a.txt does not exist
    <exit 1>
