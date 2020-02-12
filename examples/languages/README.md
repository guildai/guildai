# Guild Example: `languages`

This example shows how Guild works with various runtime languages.

- [guild.yml](guild.yml) - Project Guild file
- [Train.java](Train.java) - Java example
- [train.r](train.r) - R example
- [train.sh](train.sh) - Bash example
- [train-2.sh](train-2.sh) - Alternative Bash example using environment variables

## Flag Interfaces

Guild uses two general interfaces to pass flag values to programs:

- Command line arguments
- Environment variables

The examples in this project show the use of both. Refer to the
sections below for details.

## Source Code

Operations are run in the context of a *run directory*, not the
project directory. Required files must be copied or linked into the
run directory using one of two methods:

- Source code copy, which Guild performs automatically
- File dependency

In the case of scripts, examples reference copied source code using
the pattern `.guild/sourcecode/<script>`.

## R Examples

To run the R example, use:

```
$ guild run r
```

Press `Enter` to run the sample training operation using the default
values.

`r` is an R port of the sample function used in [Guild Get
Started](https://guild.ai/docs/start/). Refer to the steps in that
guide to apply Guild features to this example.

## Bash Examples

There are two examples that use Bash scripts:

- `bash` - uses command line arguments to pass flag values
  (see [train.sh](train.sh))
- `bash-2` - used environment variables to pass flag values (see
  [train-2.sh](train-2.sh))

Both examples print flag values and exit without doing any work. They
serve as patterns for scripts in any language.

To run the Bash examples, use:

```
$ guild run bash
```

and:

```
$ guild run bash-2
```

## Java Example

The Java examples uses a Bash command to compile Java source code and
then run the compiled code. Refer to the `java` operation in
[guild.yml](guild.yml) for configuration details and to
[Train.java](Train.java) for the implementation.

To run the Java example, use:

```
$ guild run java
```
