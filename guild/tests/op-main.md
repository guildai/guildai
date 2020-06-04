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

The project contains some invalid operation specs and as a result,
generates warnings whenver an operation is run.

When we run `fail.py`, the script generates an error by raising an
exception.

    >>> project.run("fail.py")
    Traceback (most recent call last):
      File ".../.guild/sourcecode/fail.py", line 17, in <module>
        fail()
      File ".../.guild/sourcecode/fail.py", line 7, in fail
        fail2()
      File ".../.guild/sourcecode/fail.py", line 14, in fail2
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
        python_util.exec_script(module_info.mod_path, globals, mod_name=mod_name)
      File ".../guild/python_util.py", line ..., in exec_script
        exec(code, script_globals)
      File ".../.guild/sourcecode/fail.py", line 17, in <module>
        fail()
      File ".../.guild/sourcecode/fail.py", line 7, in fail
        fail2()
      File ".../.guild/sourcecode/fail.py", line 14, in fail2
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
      File ".../.guild/sourcecode/fail.py", line 17, in <module>
        fail()
      File ".../.guild/sourcecode/fail.py", line 7, in fail
        fail2()
      File ".../.guild/sourcecode/fail.py", line 14, in fail2
        raise Exception("FAIL")
    Exception: FAIL
    <exit 1>

    >>> project.run("fail", flags={"code": 2})
    FAIL
    <exit 2>

## Relative imports

Guild loads modules using their package name so that `__package__` is
correctly defined.

    >>> project = Project(sample("projects/op-main-package"))

The `op-main-package` contains operation defs that generate warnings
due to mis-specifications (see tests below). These warnings are logged
whenever the project Guild file is loaded. We can run a `pass` (no-op)
operation to generate these warnings.

    >>> project.run("pass")
    WARNING: cannot import flags from abc_123: No module named abc_123
    WARNING: cannot import flags from pkg: No module named pkg.__main__
    ('pkg' is a package and cannot be directly executed)

The warnings are suppressed as needed by setting
`NO_WARN_FLAGS_IMPORT` below for tests.

Guild uses different methods of loading modules depending on whether
the module is loaded with global flag assignments.

Here's the case where globals are not used (i.e. dest args):

    >>> with Env({"NO_WARN_FLAGS_IMPORT": "1"}):
    ...     project.run("args")
    hello from __main__ in pkg
    hello from pkg.main_impl in pkg

Here's the case where globals are used:

    >>> with Env({"NO_WARN_FLAGS_IMPORT": "1"}):
    ...    project.run("globals")
    hello from __main__ in pkg
    hello from pkg.main_impl in pkg

The same scheme applies when `main` contains a path to the package, as
is the case with `op-args-2`.

    >>> with Env({"NO_IMPORT_FLAGS_CACHE": "1", "NO_WARN_FLAGS_IMPORT": "1"}):
    ...     project.run("args-2")
    hello from __main__ in pkg
    hello from pkg.main_impl in pkg

We can execute a package provided it contains a `__main__` module.

    >>> with Env({"NO_WARN_FLAGS_IMPORT": "1"}):
    ...    project.run("pkg-main")
    a package!

A package that does not contain a `__main__` module causes an error.

    >>> with Env({"NO_WARN_FLAGS_IMPORT": "1"}):
    ...     project.run("pkg")
    guild: No module named pkg.__main__ ('pkg' is a package and cannot
    be directly executed)
    <exit 1>
