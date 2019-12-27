# Debug Source Code

Guild provides an option for specifying an alternative location for
project source code files. This is used to control from where project
modules are loaded as an alternative to the run directory.

Let's illustrate by creating a simple project with a `say.py` module
that prints a message.

    >>> project = Project(mkdtemp())
    >>> write(path(project.cwd, "say.py"), "print('hi 1')")

Let's generate a run:

    >>> project.run("say.py")
    hi 1

Here's the run source code:

    >>> run_1 = project.list_runs()[0]
    >>> project.cat(run_1, ".guild/sourcecode/say.py")
    print('hi 1')

Next we'll create directory that contains an alternative `say.py`
module, which we'll use as our debug location:

    >>> alt_source = mkdtemp()
    >>> write(path(alt_source, "say.py"), "print('hi 2')")

Let's run the `say.py` script again, but this time specifying
`debug_sourcecode` for the new subdir:

    >>> project.run("say.py", debug_sourcecode=alt_source)
    hi 2

Note the alternative message.

Let's confirm that the second run contains the expected project source
code:

    >>> run_2 = project.list_runs()[0]
    >>> project.cat(run_2, ".guild/sourcecode/say.py")
    print('hi 1')

And finally confirm that runs 1 and 2 are in fact different runs.

    >>> run_1.dir != run_2.dir
    True
