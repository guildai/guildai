# Separating Inputs and Outputs Tests

## Overview

This document illustrates a number of cases involving run inputs and
outputs. The tests below rely on the convention of a pipeline of runs
consisting of upstream runs and downstream runs. Upstream runs
generate inputs for downstream runs, which generate outputs. Runs can
be chained together in this way to form a pipeline. The tests below
focus on a single upstream run and multiple variations of a single
downstream run.

Files used in these tests:

|                                  |                                                                                             |
|----------------------------------|---------------------------------------------------------------------------------------------|
| [guild.yml](guild.yml)           | Guild file                                                                                  |
| [upstream.py](upstream.py)       | Sole implementation of upstream operation                                                   |
| [downstream.py](downstream.py)   | Implementation of downstream operation can overwrite an upstream model                      |
| [downstream2.py](downstream2.py) | Implementation of downstream operation that formally differentiates input and output models |

To run the tests in this document, change to this directory and run:

    guild check -nt TEST.md

## Setup

The runs generated below are written to a temporary directory.

    >>> os.environ["GUILD_HOME"] = mkdtemp()
    >>> print("Runs written to %s" % os.environ["GUILD_HOME"],
    ...       file=sys.stderr)

## Accidental Overwrite Using Links

This section illustrates how you can accidentally overwrite files in
upstream runs in Guild 0.7.x. By default, Guild 0.7 defaults to using
symbolic links when resolving required operation files. When
directories are resolved as links, downstream runs have direct access
upstream files. Changes to those files are made to the upstream run
rather than the current run.

To illustrate, generate an upstream run.

    >>> run("guild run upstream -y")
    <exit 0>

The upstream operation writes the string 'upstream' to a generated
sample model checkpoint for illustration purposes.

    >>> run("guild cat -p models/checkpoint.txt")
    upstream
    <exit 0>

Next, run `downstream-link`. This operation uses the default
resolution method of symlinking to upstream files. `downstream-link`
selects a directory from `upstream,` giving it access to files in the
upstream run directory.

    >>> run("guild run downstream-link -y")
    Resolving upstream dependency
    Using run ... for upstream resource
    <exit 0>

The downstream operation writes the string 'downstream' to the sample
model checkpoint.

    >>> run("guild cat -p models/checkpoint.txt")
    downstream
    <exit 0>

This operation has accidentally corrupted the upstream model.

    >>> run("guild cat -Fo upstream -p models/checkpoint.txt")
    downstream
    <exit 0>

## Fix Overwrite Using Copy

The `downstream-copy` operation addresses the problem associated links
by setting the resource attribute `target-type` to `copy`.

Generate a new upstream run because the first upstream run is corrupt.

    >>> run("guild run upstream -y")
    <exit 0>

    >>> run("guild cat -p models/checkpoint.txt")
    upstream
    <exit 0>

Run `downstream-copy`. This operation resolves the upstream files by
copying instead of linking. While this resolution method is more
expensive --- it requires time and storage for copies --- it insulates
the upstream run from changes made by the downstream operation.

    >>> run("guild run downstream-copy -y")
    Resolving upstream dependency
    Using run ... for upstream resource
    <exit 0>

    >>> run("guild cat -p models/checkpoint.txt")
    downstream
    <exit 0>

The upstream run sample model is unchanged.

    >>> run("guild cat -Fo upstream -p models/checkpoint.txt")
    upstream
    <exit 0>

## Explicit Separation of Inputs and Outputs

Another method for separating operation inputs and outputs is to use
explicit files or directories for each.

### Separate Input and Output Files

The operation `downstream-separation-with-files` uses separate files
located in the run directory for input and output.

The operation runs [`downstream2.py`](downstream2.py), which formally
defines model input and output paths using command arguments.

    >>> run("guild run downstream-separation-with-files -y")
    Resolving upstream dependency
    Using run ... for upstream resource
    upstream model ok
    <exit 0>

Note that `downstream2.py` verifies the input model to ensure it
doesn't operate on unexpected input. In real cases, this is not always
feasible but it's a good practice to adopt where possible.

The input and output files are clearly separate.

    >>> run("guild ls -n")
    checkpoint-in.txt
    checkpoint-out.txt
    <exit 0>

    >>> run("guild cat -p checkpoint-in.txt")
    upstream
    <exit 0>

    >>> run("guild cat -p checkpoint-out.txt")
    downstream
    <exit 0>

### Separate Input and Output Directories

The operation `downstream-separation-with-dirs` uses separate input
and output directories to isolate files.

> NOTE. The downstream Python module does not change in this
> case. It's interface is sufficient to identify the input and output
> paths. Guild's role is to setup the run directory and convey the
> correct paths. This is managed in the Guild file and does not
> require changes to the Python code.

    >>> run("guild run downstream-separation-with-dirs -y")
    Resolving upstream dependency
    Using run ... for upstream resource
    upstream model ok
    <exit 0>

    >>> run("guild ls -n")
    inputs/
    outputs/
    outputs/checkpoint.txt
    <exit 0>

Files under `inputs` are not shown in the output for `ls` because
`inputs` is a link. By default, Guild does not follow links in file
lists. Show the complete list of files by including the `-L` (follow
links) option.

    >>> run("guild ls -nL")
    inputs/
    inputs/checkpoint.txt
    outputs/
    outputs/checkpoint.txt
    <exit 0>

Input and output models are similarly separated, this time in
directories rather than as separate files.

    >>> run("guild cat -p inputs/checkpoint.txt")
    upstream
    <exit 0>

    >>> run("guild cat -p outputs/checkpoint.txt")
    downstream
    <exit 0>

`downstream-separation-with-dirs-2` is an alternative implementation
that avoids linking or copying upstream directories. As shown earlier,
linking upstream directories exposes those upstream runs to accidental
corruption. While copying upstream directories prevents this, the copy
operation can be costly.

`downstream-separateion-with-dirs-2` creates links to only the files
needed. It could alternatively copy those files using `target-type:
copy`. It places those resolved files in an `inputs` downstream run
subdirectory.

    >>> run("guild run downstream-separation-with-dirs-2 -y")
    Resolving upstream dependency
    Using run ... for upstream resource
    upstream model ok
    <exit 0>

    >>> run("guild ls -n")
    inputs/
    inputs/checkpoint.txt
    outputs/
    outputs/checkpoint.txt
    <exit 0>

In this case that files under `inputs` are shown because `inputs`
directory, not a link. The subdirectory clearly denotes the contents
as inputs.

    >>> run("guild cat -p inputs/checkpoint.txt")
    upstream
    <exit 0>

    >>> run("guild cat -p outputs/checkpoint.txt")
    downstream
    <exit 0>

## Notes

Future versions of Guild will set run files to read-only as a measure
of protection against accidental modification by downstream
operations. This behavior will support overrides in the Guild file.

Future versions of Guild will also support run validation through
SHA-256 digests. This is an additional safeguard to detect changes to
run files.
