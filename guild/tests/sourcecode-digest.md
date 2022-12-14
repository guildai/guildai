# Source code digest

Guild generates a digest of soure code files so that any change to
source code is reflected as a change to the digest.

For our tests, we'll work with a dynamically modified project.

    >>> use_project(mkdtemp())

## Baseline digest

Create a initial Guild file that defined an operation `op` that does
nothing.

    >>> write("guild.yml", """
    ...   op:
    ...     main: guild.pass
    ... """)


Guild uses the function `file_util.files_digest` to calculate a digest
for a list of files.

    >>> from guild.file_util import files_digest

A helper function to generate a sourcecode digest for a directory:

    >>> def sourcecode_digest(root_dir):
    ...     return files_digest(sorted(findl(root_dir)), root_dir)

    >>> project_digest_1 = sourcecode_digest(".")

Verify that list of source code selected for the `op` run.

    >>> run("guild run op --test-sourcecode")
    Copying from the current directory
    Rules: ...
    Selected for copy:
      guild.yml
    Skipped:
    <exit 0>

Generate a run for `op`.

    >>> run("guild run op --label project-1 -y")
    <exit 0>

    >>> run("guild runs -s")
    [1]  op  completed  project-1

Verify the list of source code files for the run.

    >>> run("guild ls --sourcecode -n")
    guild.yml

Verify that the source code digest for the run matches what we expect
for the project.

    >>> run_digest_1 = run_capture("guild select --attr sourcecode_digest")
    >>> run_digest_1 == project_digest_1
    True

The digest can be used to filter runs.

    >>> run(f"guild runs -Fd {project_digest_1} -s")
    [1]  op  completed  project-1

If specify a different digest, we get an empty result.

    >>> run(f"guild runs -Fd abcde123")
    <exit 0>

## New source code file

Add a new file to the project.

    >>> write("hello.py", "print('hello')\n")

Modify `op` to run the new file.

    >>> write("guild.yml", """
    ... op:
    ...   main: hello
    ... """)

The project directory:

    >>> find(".")
    guild.yml
    hello.py

Update the project digest.

    >>> project_digest_2 = sourcecode_digest(".")

The project digest changes.

    >>> project_digest_2 != project_digest_1
    True

Confirm the source files selected for `op` - these should include the
new file.

    >>> run("guild run op --test-sourcecode")
    Copying from the current directory
    Rules: ...
    Selected for copy:
      guild.yml
      hello.py
    Skipped:
    <exit 0>

Create a new run.

    >>> run("guild run op --label project-2 -y")
    hello

The run sourcecode:

    >>> run("guild ls -n --sourcecode")
    guild.yml
    hello.py

Verify that the sourcecode digest matches the project digest.

    >>> run_digest_2 = run_capture("guild select --attr sourcecode_digest")

    >>> run_digest_2 == project_digest_2
    True

Filter runs using the two digests.

    >>> run(f"guild runs -s -Fd {project_digest_1}")
    [1]  op  completed  project-1

    >>> run(f"guild runs -s -Fd {project_digest_2}")
    [1]  op  completed  project-2

## Modified source code file

When we modify a file in the project, the source code digest changes.

Re-write `hello.py` to print a different message.

Let's simulate a change to our source code file `hello.py`.

    >>> write("hello.py", "print('hola')\n")

Re-calculate the project sourcecode digest.

    >>> project_digest_3 = sourcecode_digest(".")

The project digest changes.

    >>> project_digest_3 != project_digest_2
    True

Generate a new run.

    >>> run("guild run op --label project-3 -y")
    hola

Verify that the run sourcecode digest equals the latest project
sourcecode digest.

    >>> run_digest_3 = run_capture("guild select --attr sourcecode_digest")

    >>> run_digest_3 == project_digest_3
    True

Show runs using a filter expressions.

    >>> run("guild runs -s -F 'sourcecode_digest in "
    ...     f"[\"{project_digest_1}\",\"{project_digest_3}\"]'")
    [1]  op  completed  project-3
    [2]  op  completed  project-1
