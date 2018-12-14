# Cross package inheritance

These tests cover the **Extending packages** topic in `guildfiles.md`
in more depth.

We'll work with the `guildfile` interface:

    >>> from guild import guildfile

Guild is a system that enables reuse of project configuration by way
of *model extension*.

We'll work packages defined in the `cross-package-inherits` project:

    >>> projects = sample("projects/cross-package-inherits")

## Project structure

Package `a` represents the root of the package hierarchy.

    >>> gf_a = guildfile.from_dir(join_path(projects, "a"))

    >>> gf_a.models
    {'model': <guild.guildfile.ModelDef 'model'>}

We can explicitly test for parents:

    >>> gf_a.models["model"].parents
    []

Package `b` defines a model that extends `a/model`.

In order to load package `b`, we must include package `a` in the
system path. Without including it, we get an error when we try to load
`b`:

    >>> gf_b = guildfile.from_dir(join_path(projects, "b"))
    Traceback (most recent call last):
    GuildfileReferenceError: error in
    .../samples/projects/cross-package-inherits/b/guild.yml: cannot
    find Guild file for package 'a'

Let's modify the system path to include our sample projects:

    >>> import sys
    >>> sys_path_save = sys.path
    >>> sys.path = [projects] + sys.path

We can now load `b`:

    >>> gf_b = guildfile.from_dir(join_path(projects, "b"))

    >>> gf_b.models
    {'model': <guild.guildfile.ModelDef 'model'>}

Model `b` parents include the Guildfile defining `a`:

    >>> gf_b.models["model"].parents
    [<guild.guildfile.Guildfile '.../cross-package-inherits/a/guild.yml'>]

Package `c` in turn defines a model that extends `b/model`.

    >>> gf_c = guildfile.from_dir(join_path(projects, "c"))

    >>> gf_c.models
    {'model': <guild.guildfile.ModelDef 'model'>}

    >>> gf_c.models["model"].parents
    [<guild.guildfile.Guildfile '.../cross-package-inherits/a/guild.yml'>,
     <guild.guildfile.Guildfile '.../cross-package-inherits/b/guild.yml'>]

There are two additional packages, which extend one another, creating
a cycle:

    >>> guildfile.from_dir(join_path(projects, "cycle_a"))
    Traceback (most recent call last):
    GuildfileCycleError: error in .../cross-package-inherits/cycle_a/guild.yml:
    cycle in 'extends' (cycle_b/model -> cycle_a/model -> cycle_b/model)

    >>> guildfile.from_dir(join_path(projects, "cycle_b"))
    Traceback (most recent call last):
    GuildfileCycleError: error in .../cross-package-inherits/cycle_b/guild.yml:
    cycle in 'extends' (cycle_a/model -> cycle_b/model -> cycle_a/model)

## Running operations

We'll now run the `test` operation on each of our models:

    >>> gf_a.models["model"].operations
    [<guild.guildfile.OpDef 'model:test'>]

    >>> gf_b.models["model"].operations
    [<guild.guildfile.OpDef 'model:test'>]

    >>> gf_c.models["model"].operations
    [<guild.guildfile.OpDef 'model:test'>]

This operation is defined in model `a` and inherited by the other
models by way of the model extension hierarchy. However, each model
modifies the operation by either defining a new parameter or by
providing an alternative local file resource.

We'll use the `gapi` interface to run the operations:

    >>> from guild import _api as gapi

Let's run `a/model:test`.

    >>> a_test_run_dir = mkdtemp()

    >>> out, _ = gapi.run(
    ...   spec="model:test",
    ...   cwd=join_path(projects, "a"),
    ...   run_dir=a_test_run_dir)

    >>> print(out)
    Hello from a/model
    File from model/a

Here we see the message and file printed for `a`.

Next we'll run `b/model:test`:

    >>> b_test_run_dir = mkdtemp()

    >>> try:
    ...   out, err = gapi.run(
    ...     spec="model:test",
    ...     cwd=join_path(projects, "b"),
    ...     run_dir=b_test_run_dir)
    ... except gapi.RunError as e:
    ...   print(e.err)
    ... else:
    ...   out, err
    ERROR: error loading guildfile from .:
    error in .../cross-package-inherits/b/guild.yml: cannot find
    Guild file for package 'a'
    main_bootstrap.py: guildfile in the current directory contains
    an error (see above for details)

In this case we receive an error because Guild can't find the package
`a` specified in the model extension spec `a/model`.

Let's re-run the operation and include our projects directory in the
system path:

    >>> out, _ = gapi.run(
    ...   spec="model:test",
    ...   cwd=join_path(projects, "b"),
    ...   run_dir=b_test_run_dir,
    ...   extra_env={"PYTHONPATH": ".."})

    >>> print(out)
    Hello from b/model
    File from model/a

In this case, `b/model` redefines the message but does not provide its
own message file.

Next we'll run `c/model:test`:

    >>> c_test_run_dir = mkdtemp()

    >>> out, _ = gapi.run(
    ...   spec="model:test",
    ...   cwd=join_path(projects, "c"),
    ...   run_dir=c_test_run_dir,
    ...   extra_env={"PYTHONPATH": ".."})

    >>> print(out)
    Hello from c/model
    File from model/c

## Cleaup

Restore the system path:

    >>> sys.path = sys_path_save
