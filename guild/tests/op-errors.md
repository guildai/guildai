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
      File ".../.guild/sourcecode/stack.py", line 12, in <module>
        fail()
      File ".../.guild/sourcecode/stack.py", line 4, in fail
        c1()
      File ".../.guild/sourcecode/stack.py", line 7, in c1
        c2()
      File ".../.guild/sourcecode/stack.py", line 10, in c2
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

    >>> project.run("exception.py", flags={"dummy": [1]}, force_flags=True)
    INFO: [guild] Running trial ...: exception.py (dummy=1)
    Traceback (most recent call last):
      File ".../.guild/sourcecode/exception.py", line 1, in <module>
        raise Exception("big time fail")
    Exception: big time fail
    <exit 1>
