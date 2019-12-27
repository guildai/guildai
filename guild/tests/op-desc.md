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

## Basics

Let's start by running `train.py` - a script located in the project root.

    >>> run, _ = project.run_capture("train.py")

When we print the runs, we see the operation is listed as we specified
for the run call.

    >>> project.print_runs()
    train.py

Let's look at this run more closely.

Here's its opref file:

    >>> cat(run.guild_path("opref"))
    script:.../samples/projects/op-desc... '' '' train.py

Here's the information decoded in the run's opref attribute:

    >>> run.opref
    OpRef(pkg_type='script',
          pkg_name='.../samples/projects/op-desc',
          pkg_version='',
          model_name='',
          op_name='train.py')

In the case of `script` operations, the `pkg_name` opref attribute is
the project directory.

    >>> compare_paths(run.opref.pkg_name, project.cwd)
    True

This path is always stored as an absolute path.

    >>> os.path.isabs(run.opref.pkg_name)
    True

Here is how the run is displayed when listing from the project
directory:

    >>> project.print_runs()
    train.py

Guild alters the way operations are shown when the current directory
is different from opref project location.

Here's how the run is displayed when listing from the project parent
directory:

    >>> project.print_runs(cwd="..")
    train.py (op-desc)

This shows that the `train.py` operation originated from the `op-desc`
subdirectory.

Next we'll show the run from a project subdirectory.

    >>> project.print_runs(cwd="a")
    train.py (../)

Note that a path to the parent directory is shown.

Refer to [Utils - Shorten dirs](utils.md#shorten-dirs) for how
directories are shortened.

## Test matrix

To test various scenarios, we use a matrix of tests (see below).

We use `runs_impl.format_run` to format op descriptions. We modify the
function slightly to remove user dir symbols ("~") so we can assert
absolute paths using leading "/" chars.

    >>> def op_desc(run, show_from_dir):
    ...     from guild.commands.runs_impl import format_run
    ...     with SetCwd(os.path.join(project.cwd, show_from_dir)):
    ...         desc = format_run(run)["op_desc"].replace("~", "")
    ...         # Guild uses a unicode ellipses that causes errors in Python 2
    ...         # doctest diffs - return encoded as ascii replacing errors with '?'
    ...         if sys.version_info[0] == 2:
    ...             desc = desc.encode("ascii", "replace")
    ...         return desc

Here's our test loop, which runs the matrix above and prints the
result as a table.

    >>> def run_tests(tests):
    ...     results = [{
    ...         "op_spec": "Spec",
    ...         "run_from": "Run From",
    ...         "show_from": "Shown From",
    ...         "op_desc": "Displayed As",
    ...     }]
    ...     for run_from_dir, op_spec, show_from in tests:
    ...         run, _ = project.run_capture(op_spec, cwd=run_from_dir)
    ...         for show_from_dir in show_from:
    ...             results.append({
    ...                 "op_spec": op_spec,
    ...                 "run_from": run_from_dir,
    ...                 "show_from": show_from_dir,
    ...                 "op_desc": op_desc(run, show_from_dir),
    ...             })
    ...     cli.table(results, ["op_spec", "run_from", "show_from", "op_desc"])

Here are our tests:

    >>> tests = [
    ...     # run_from  # op_spec        # show_from
    ...     (".",       "train.py",      (".", "a", "a/b")),
    ...     ("a",       "train.py",      ("a", ".", "a/b", "b")),
    ...     ("a/b",     "train.py",      ("a/b", ".", "a", "b")),
    ...     (".",       "a/train.py",    (".", "a", "a/b")),
    ...     (".",       "a/b/train.py",  (".", "a", "a/b", "b")),
    ...     (".",       "a:train",       (".", "a", "a/b")),
    ...     ("a",       "../train.py",   ("a", ".", "a/b", "b")),
    ... ]

And the results:

    >>> run_tests(tests)
    Spec          Run From  Shown From  Displayed As
    train.py      .         .           train.py
    train.py      .         a           train.py (../)
    train.py      .         a/b         train.py (/.../op-desc)
    train.py      a         a           train.py
    train.py      a         .           train.py (a)
    train.py      a         a/b         train.py (../)
    train.py      a         b           train.py (../a)
    train.py      a/b       a/b         train.py
    train.py      a/b       .           train.py (a/b)
    train.py      a/b       a           train.py (b)
    train.py      a/b       b           train.py (../a/b)
    a/train.py    .         .           a/train.py
    a/train.py    .         a           a/train.py (../)
    a/train.py    .         a/b         a/train.py (/.../op-desc)
    a/b/train.py  .         .           a/b/train.py
    a/b/train.py  .         a           a/b/train.py (../)
    a/b/train.py  .         a/b         a/b/train.py (/.../op-desc)
    a/b/train.py  .         b           a/b/train.py (../)
    a:train       .         .           a:train
    a:train       .         a           a:train (../)
    a:train       .         a/b         a:train (/.../op-desc)
    ../train.py   a         a           train.py (../)
    ../train.py   a         .           train.py
    ../train.py   a         a/b         train.py (/.../op-desc)
    ../train.py   a         b           train.py (../)
