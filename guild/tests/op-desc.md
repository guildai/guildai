# Operation Descriptions

Guild supports operations from various sources:

- Scripts
- Guild files
- Packages

When Guild runs an operation, it records the operation info in a file
named `opref` under the run directory. This file contains information
about the operation source, including:

- Package type
- Package name
- Package version
- Model name
- Operation name

This information is used to generate an operation description when
viewing a run.

To illustrate how Guild formats operation descriptions, we'll use the
sample project `op-desc`:

    >>> project = Project(sample("projects", "op-desc"))

This project contains various scripts and project operations (defined
in the project Guild file) that we can run to see how operations are
formatted.

Let's start by running `a/train.py` - a script located in the `a`
project subdirectory.

    >>> run, _ = project.run_capture("a/train.py")

When we print the runs, we see the operation is listed as we specified
for the run call.

    >>> project.print_runs()
    a/train.py

Let's look at this run more closely.

Here's its opref file:

    >>> cat(run.guild_path("opref"))
    script:../.../samples/projects/op-desc '' '' a/train.py

Here's the information decoded in the run's opref attribute:

    >>> run.opref
    OpRef(pkg_type='script',
          pkg_name='../.../samples/projects/op-desc',
          pkg_version='',
          model_name='',
          op_name='a/train.py')

In the case of `script` operations, the `op_name` attribute is used as
the operation whenever displaying the run (see above). However, the
operation description depends on the current directory. If the current
directoy is the origin of the project - i.e. the directory specified
in the opref `pkg_name` attribute relative to the run - the operation
name is shown without qualification.

Note that the resolved opref `pkg_name` directory is in fact the same
as the project directory.

    >>> resolved_opref_origin = path(run.dir, run.opref.pkg_name)
    >>> compare_paths(resolved_opref_origin, project.cwd)
    True

However, if we show the run from another directory, the operation name
is qualified to show where the operation originated from, relative to
the current directory.

Let's show the runs from the project parent directory.

    >>> project.print_runs(cwd="..")
    a/train.py (op-desc)

Note that the operation name is the same - `a/train.py`. This always
reflets the name of the operation as run (see above). The qualified
`(op-desc)` indicates that the origin of the operation is the
`op-desc` subdirectory.

Let's show the runs from the project `a` subdirectory. From the `a`
subdirectory, the run is shown as originating from the project
directory.

    >>> project.print_runs(cwd="a")
    a/train.py (.../projects/op-desc)


    >> project.run("b/train.py")
    >> project.run("a:train")
    >> project.run("b:train")

    >> project.print_runs()
    b:train
    a:train
    b/train.py
    a/train.py

    >> project.print_runs(cwd="..")
    b:train (op-desc)
    a:train (op-desc)
    b/train.py (op-desc)
    a/train.py (op-desc)
