# op_main.py

These tests illustrate behavior implemented by `op_main.py`.

`op_main.py` is the module used to run Python modules.

## Exception tracebacks

By default `op_main.py` removes Guild specific stack layers from
reported exceptions. The rationale for this behavior is that the Guild
stack layers are noise wrt user errors. The intent is that exceptions
resemble those that would be generated if the user script was run
directly with Python.

We use the `fail.py` script in `optimizers` sample project.

    >>> project = Project(sample("projects/optimizers"))

When we run `fail.py`, the script generates an error by raising an
exception.

    >>> project.run("fail.py")
    Traceback (most recent call last):
      File ".../.guild/sourcecode/fail.py", line 14, in <module>
        fail()
      File ".../.guild/sourcecode/fail.py", line 6, in fail
        fail2()
      File ".../.guild/sourcecode/fail.py", line 12, in fail2
        raise Exception("FAIL")
    Exception: FAIL
    <exit 1>

When we run with the debug option, we get the full stack:

    >>> project.run("fail.py", debug=True)
    DEBUG: [guild] checking '.' for model sources
    ...
    DEBUG: [guild] loading module from '.../.guild/sourcecode/fail.py'
    Traceback (most recent call last):
      ...
      File ".../guild/op_main.py", line ..., in <module>
        main()
      File ".../guild/op_main.py", line ..., in main
        _main()
      ...
      File ".../guild/op_main.py", line ..., in exec_script
        python_util.exec_script(path, globals)
      File ".../guild/python_util.py", line ..., in exec_script
        exec(code, script_globals)
      File ".../.guild/sourcecode/fail.py", line 14, in <module>
        fail()
      File ".../.guild/sourcecode/fail.py", line 6, in fail
        fail2()
      File ".../.guild/sourcecode/fail.py", line 12, in fail2
        raise Exception("FAIL")
    Exception: FAIL
    <exit 1>

Guild does not print stack information for calls to `sys.exit()` (or
`SystemExit` exceptions). Our sample script supports a `code` flag
that, when set to a value other than `1`, causes the script to exit
with a call to `sys.exit()` instead of raising an exception.

    >>> project.run("fail.py", flags={"code": 2})
    FAIL
    <exit 2>

The same behavior applies to modules run through a Guild file. In this
case, the project defines a `fail` operation that runs `fail.py`.

    >>> project.run("fail")
    Traceback (most recent call last):
      File ".../.guild/sourcecode/fail.py", line 14, in <module>
        fail()
      File ".../.guild/sourcecode/fail.py", line 6, in fail
        fail2()
      File ".../.guild/sourcecode/fail.py", line 12, in fail2
        raise Exception("FAIL")
    Exception: FAIL
    <exit 1>

    >>> project.run("fail", flags={"code": 2})
    FAIL
    <exit 2>
