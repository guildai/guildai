# Operation errors

When an operation generates an exception, Guild prints only the
traceback information applicable to the operation module. This
information does not include the initial layers of the stack
associated with Guild.

    >>> project = Project(sample("projects", "errors"))

    >>> project.run("exception.py")
    Traceback (most recent call last):
      File ".../.guild/sourcecode/exception.py", line 1, in <module>
        raise Exception("big time fail")
    Exception: big time fail
    <exit 1>

    >>> project.run("stack.py")  # doctest: +REPORT_UDIFF
    Traceback (most recent call last):
      File ".../.guild/sourcecode/stack.py", line 16, in <module>
        fail()
      File ".../.guild/sourcecode/stack.py", line 5, in fail
        c1()
      File ".../.guild/sourcecode/stack.py", line 9, in c1
        c2()
      File ".../.guild/sourcecode/stack.py", line 13, in c2
        import exception
      File ".../.guild/sourcecode/exception.py", line 1, in <module>
        raise Exception("big time fail")
    Exception: big time fail
    <exit 1>

    >>> project.run("sysexit.py")
    <BLANKLINE>
    <exit 2>

    >>> project.run("sysexit2.py")
    (3, 'yop')
    <exit 1>

In the case of batches, a batch run succeeds even when a trial
fails. The trial in this case shows the abbreviated tracback.

    >>> project.run("exception.py", flags={"dummy": [1]}, force_flags=True)
    INFO: [guild] Running trial ...: exception.py (dummy=1)
    Traceback (most recent call last):
      File ".../.guild/sourcecode/exception.py", line 1, in <module>
        raise Exception("big time fail")
    Exception: big time fail
    ERROR: [guild] Trial ... exited with an error (1) - see log for details

If we run with `fail_on_trial_error` the batch will also fail.

    >>> project.run("exception.py", flags={"dummy": [1]}, force_flags=True,
    ...             fail_on_trial_error=True)
    INFO: [guild] Running trial ...: exception.py (dummy=1)
    Traceback (most recent call last):
      File ".../.guild/sourcecode/exception.py", line 1, in <module>
        raise Exception("big time fail")
    Exception: big time fail
    ERROR: [guild] Trial ... exited with an error (1) - see log for details
    ERROR: [guild] Stopping batch because a trial failed (remaining staged
    trials may be started as needed)
    <exit 1>
