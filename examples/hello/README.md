# Guild Example: `hello`

This examples shows basic flag usage. It also demonstrates simple file
dependencies.

- [guild.yml](guild.yml) - Project Guild file
- [say.py](say.py) - Prints a greeting.
- [cat.py](cat.py) - Prints contents of a file.

Operations:

- [`hello`](#hello) - print a message from a flag - illustrates basic
  use of flags and global variables
- [`hello-file`](#hello-file) - print a message contained in a file -
  illustrates use of required files for an operation
- [`hello-op`](#hello-op) - print a message from a `hello-file`
  operation - illustrates use of files associated with a previous run

## `hello`

The `hello` operation prints a message defined by a `msg` global. It
illustrates Guild's integration with global variables.

`hello` operation:

``` yaml
hello:
  description: Say hello to my friends.
  main: say
  flags-import:
    - msg
```

The `main` attribute indicates that the operation is implemented by
the Python `say` module.

Here's `say.py`:

``` python
msg = "Hello Guild!"

print(msg)
```

Guild auto-detects that `say` uses global variables rather than
command line arguments. Guild checks for the use of `argparse` by the
module. If the module doesn't import `argparse`, Guild assumes that
flags are defined as global variables.

If you want to set this explicitly, use `flags-dest: globals`
operation attribute. For example:

``` yaml
hello:
  ...
  flags-dest: globals
  flags-import:
    - msg
```

The `flags-import` attribute tells Guild to import only the `msg`
flag. An alternative is to import *all* flags by specifying either
`all` or `yes`:

``` yaml
hello:
  ...
  flags-import: all  # will detect `msg` as the only supported flag
```

### Sample Usage

Run using the default flag value:

```
$ guild run hello
You are about to run hello
  msg: Hello Guild!
Continue? (Y/n)
```

Output:

```
Hello Guild!
```

Run with a different flag value:

```
$ guild run hello msg="Hello custom flag!"
You are about to run hello
  msg: Hello custom flag!
Continue? (Y/n)
```

Output:

```
Hello custom flag!
```

### View Results

The `hello` prints a message but does not create any files or log
scalars.

You can view information for the latest run using `guild runs
info`. This shows the run metadata including flags.

To can list the files associated with the latest run using `guild
ls`. This list is empty because the operation doesn't generate files.

To view run output, run:

```
$ guild cat --output
```

Output:

```
Hello custom flag!
```

To view output for the original run:

```
$ guild cat --output 2
```

The `2` indicates that the run with index 2 from `guild runs` should
be used. You can alternatively specify the run ID to ensure you're
viewing output for a particular` run.

Output:

```
Hello Guild!
```

## `hello-file`

## `hello-op`
