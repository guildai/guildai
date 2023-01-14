# Guild Cwd

A user may effectively chance Guild's current directory using the `-C`
flag to the `guild` command.

Create a sample project.

    >>> use_project(mkdtemp())

## Running scripts

Create a subdirectory. We'll use this as the target user directory for
running a script.

    >>> mkdir("subdir-1")

Create a sample script to run under the subdirectory.

    >>> write(path("subdir-1", "hello.py"), """
    ... print("Hello!")
    ... """)

Run the script as `hello.py` from the project root, specifying
`subdir-1` as the cwd.

    >>> run("guild -C subdir-1 run hello.py -y")
    Hello!

Source code files are copied from the subdir location.

    >>> run("guild -C subdir-1 run hello.py --test-sourcecode")
    Copying from 'subdir-1'
    Rules:
      exclude dir .*
      exclude dir * containing .guild-nocopy
      include text * size < 1048577, max match 100
      exclude dir __pycache__
      exclude dir * containing bin/activate
      exclude dir * containing Scripts/activate
      exclude dir build
      exclude dir dist
      exclude dir *.egg-info
    Selected for copy:
      subdir-1/hello.py
    Skipped:

The are copied to the run directory.

    >>> run("guild ls -n")
    hello.py

## Guild files

Create another subdirectory. This will be the target user directory
for a Guild file.

    >>> mkdir("subdir-2")

Create a `src` directory under the subdirectory. This will contain the
source code for the project operations.

    >>> mkdir(path("subdir-2", "code"))

Write a source code file for a test operation.

    >>> write(path("subdir-2", "code", "test.py"), """
    ... msg = "A test op!"
    ... print(msg)
    ... """)

Create a Guild file in the subdirectory.

    >>> write(path("subdir-2", "guild.yml"), """
    ... test:
    ...   description: A sample op
    ...   sourcecode:
    ...     dest: src
    ...     root: code
    ...   flags-import: all
    ... """)

Show the `subdir-2` directory contents.

    >>> find("subdir-2")
    code/test.py
    guild.yml

Run `test` from `subdir-2` using `-C`.

    >>> run("guild -C subdir-2 run test -y")
    A test op!

    >>> run("guild ls -n")
    src/
    src/test.py

Show help.

    >>> run("guild -C subdir-2 help")
    OVERVIEW
    ...
    BASE OPERATIONS
    <BLANKLINE>
        test
          A sample op
    <BLANKLINE>
          Flags:
            msg  (default is 'A test op!')

Modify the project source code.

    >>> write(path("subdir-2", "code", "test.py"), """
    ... msg = "A test op!"
    ... print(msg + " (modified)")
    ... """)

Diff the latest run with the project.

    >>> run("guild -C subdir-2 diff --working --cmd echo")
    ???/runs/.../src .../subdir-2/code

    >>> run("guild -C subdir-2 diff --working --path test.py --cmd echo")
    ???/runs/.../src/test.py .../subdir-2/code/test.py

Re-run the last run using the modified project source code.

    >>> last_run = run_capture("guild select")

    >>> run(f"guild -C subdir-2 run --restart {last_run} --force-sourcecode -y")
    A test op! (modified)

    >>> run("guild cat -p src/test.py")
    msg = "A test op!"
    print(msg + " (modified)")

Re-run using a different value for `msg`.

    >>> run(f"guild -C subdir-2 run --restart {last_run} msg=Hola -y")
    Hola (modified)
