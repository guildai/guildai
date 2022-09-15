# R script support

Guild provides support for R script via the `r_script` plugin.

We'll use the `r-script` sample project in these tests.

    >>> cd(sample("projects", "r-script"))

We use a temp Guild home to isolate runs.

    >>> set_guild_home(mkdtemp())

## Run r script directory

The plugin lets us run an R script directly.

TODO - fix!

    >>> run("guild run simple.R -y")
    WARNING: unknown flag type 'bool' for skip_connections - cannot coerce
    WARNING: unknown option '--layers'
    <BLANKLINE>
    Error in `[[.default`(mode, ((i + 1)%%length(mode)) + 1L) :
      subscript out of bounds
    Calls: <Anonymous> ... [[.fs_perms -> new_fs_perms -> assert -> unlist -> NextMethod
    Execution halted
    <exit 1>
