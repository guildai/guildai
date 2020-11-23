# Debugging Guild Operations

## Breakpoints

Python based operations support breakpoints with Python's
[`pdb`](https://docs.python.org/library/pdb.html) module.

A breakpoints stops code execution and lets you step through code,
perform explore program state, run arbitrary code, and set additional
breakpoints.

Guild supports three breakpoint types:

- Break at a specified module line number or function
- Break automatically if an error occurs

### Break at Line Number

Use `guild run --break 1` to break on the first line of the main
module. Use a different number as needed.

To try this, change to this project and run:

``` command
guild run test.py --break 1
```

To break in a different module, specify the module or script path
along with the line number in the format `MODULE:LINE`. For example,
to break on line 10 of a module named `models.py`, use `guild run
--break models:10`. Note that you can omit the `.py` extension.

To see this working, run:

``` command
guild run test.py --break submod:1
```

### Break on a Function Call

To break on a function call, specify the function with the `--break`
option in the format `MODULE.FUNCTION_NAME`.

To try this, run:

``` command
guild run test.py --break submod.add
```

### Break On Error

Use the [`run`](https://my.guild.ai/commands/run) comment
`--break-on-error` option to enter into a post mortem debug session
when an unhandled Python error occurs.

To illustrate, run `error.py` with `--break-on-error`:

``` command
guild run error.py --break-on-error
```

The script intentially generates a `ZeroDivisionError` error. When the
error occurs, Guild shows the error and Python traceback and starts a
post mortem debug session. From this session you can use the [pdb
commands] to evaluate the Python state at the time the error occurs.
