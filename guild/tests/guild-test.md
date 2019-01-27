# Guild test

The module `guild.test` is used to test models defined in Guild files.

    >>> from guild import test

Tests are defined in Guild files along with the models they test. For
our tests, we'll work with the 'tests' sample project:

    >>> project_dir = sample("projects/tests")

These tests will exercise the Guild `test` command directly. We'll use
a temporary Guild directory for test runs.

    >>> guild_dir = mktemp_guild_dir()

Here's a helper function to run tests:

    >>> def run_tests(tests=None):
    ...   import subprocess
    ...   from guild import _api as gapi
    ...   test_args = []
    ...   for t in tests or []:
    ...     test_args.extend(["-t", t])
    ...   try:
    ...     out = gapi.guild_cmd("test", ["-y"] + test_args,
    ...                    cwd=project_dir,
    ...                    guild_home=guild_dir,
    ...                    capture_output=True)
    ...   except subprocess.CalledProcessError as e:
    ...     print("ERROR (%i): %s" % (e.returncode, e.output.decode()))
    ...   else:
    ...     print(out.decode())

Let's first example the tests defined in the project.

    >>> gf = guildfile.from_dir(project_dir)
    >>> gf.tests
    [<guild.guildfile.TestDef 'output-1'>,
     <guild.guildfile.TestDef 'output-2'>,
     <guild.guildfile.TestDef 'file-1'>,
     <guild.guildfile.TestDef 'fail-1'>,
     <guild.guildfile.TestDef 'all'>]

Let's run some tests:

    >>> run_tests(["output-1", "output-2", "file-1"])
    Testing output-1
    Running operation gen-output
    hi
    Checking ...
    output: hi
    Testing output-2
    Running operation gen-output
    hello car
    Checking ...
    output: hello
    output: car
    Testing file-1
    Running operation gen-files
    Resolving sample-file dependency
    Checking ...
    file: file-1 (contains 'bus')
    file: sample.txt
    3 test(s) passed
    <BLANKLINE>

This test fails:

    >>> run_tests(["fail-1"])
    ERROR (1): Testing fail-1
    Running operation gen-output
    hi
    Checking ...
    output: bye
    Test fail-1 failed: could not find pattern 'bye' in .../.guild/output
    1 test(s) failed - see above for details

The `all` test uses a `for-each-model` step to run a list of
operations on each model.

    >>> run_tests(["all"])
    Testing all
    Running operation test:gen-output
    hi
    Running operation test:gen-files
    Resolving sample-file dependency
    1 test(s) passed
    <BLANKLINE>
