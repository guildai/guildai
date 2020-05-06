# Guild Example: `hello`

This example illustrates basic Guild configuration.

- [guild.yml](guild.yml) - Project Guild file
- [say.py](say.py) - Prints a greeting
- [cat.py](cat.py) - Prints contents of a file
- [hello.txt](hello.txt) - Sample file used by `hello-file` operation

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
  description: Say hello to my friends
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

The `hello-file` operation prints a message from a file. It
illustrates the use of a user defined file as input to an operation.

Here's the operation configuration:

``` yaml
hello-file:
  description: Shows a message from a file
  main: cat
  flags-import:
    - file
  requires:
    - file: ${file}
      name: file
```

The operation is implemented in [cat.py](cat.py).

The `file` flag is used to specify the file used as input to the
operation. The file is a *required resource* and must be configured in
the `requires` operation attribute.

From the example directory, run:

    $ guild run hello-file

You can specify the file to use:

    $ guild run hello-file file=hello.txt

The file requirement is named `file` to improve the message printed
when resolving the resource.

For example:

```
Resolving file dependency
Using hello.txt for file resource
Reading message from hello.txt
Hello, from a file!
```

## `hello-op`

The `hello-op` operation shows how the result from an operation can be
used by another operation.

By convention Guild refers to the required operation as _upstream_ and
the requiring operation as _downstream_.

`hello-op` requires output from `hello-file`. In this case,
`hello-file` is the _upstream_ operation and `hello-op` is the
_downstream_ operation.

Here's the operation definition:

``` yaml
hello-op:
  description: Show a message from a hello-file operation
  main: cat
  requires:
    - operation: hello-file
      rename: '.* hello.txt'
```

When you run `hello-op`, Guild looks for a `hello-file` run. Guild
creates links from `hello-file` in the run directory for the
`hello-op` run.

To use a standard file name for input, the operation renames the
upstream file to `hello.txt`. (This scheme assumes that `hello-file`
contains a single file. If the run happens has more than one file, the
first file, sorted in lexiconigraphic ascending order, is renamed and
subsequent files are skipped with a warning message.)

By default, Guild selects the latest non-error run for
`hello-file`. You can specify an alternative run using the
`hello-file` resource name:

```
$ guild run hello-op hello-file=<run ID>
```
