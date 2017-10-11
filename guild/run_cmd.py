import click

import guild.click_util

def run_params(fn):
    guild.click_util.append_params(fn, [
        click.Argument(("args",), metavar="[ARG...]", nargs=-1),
        click.Option(
            ("-p", "--project", "project_location"),
            help="Project location (file system directory) for MODEL.",
            metavar="LOCATION"),
        click.Option(
            ("--disable-plugins",),
            help="A comma separated list of plugin names to disable."),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before running operation.",
            is_flag=True),
        click.Option(
            ("--print-cmd",),
            help="Show the operation command and exit (does not run).",
            is_flag=True),
        click.Option(
            ("--print-env",),
            help="Show the operation environment and exit (does not run).",
            is_flag=True),
    ])
    return fn

@click.command()
@click.argument("opspec", metavar="[MODEL:]OPERATION")
@run_params

@guild.click_util.use_args

def run(args):
    """Run a model operation.

    By default Guild will try to run OPERATION for the default model
    defined in a project. If a project location is not specified (see
    --project option below), Guild looks for a project in the current
    directory.

    If MODEL is specified, Guild will use it instead of the default
    model defined in a project.
    """
    import guild.run_cmd_impl
    guild.run_cmd_impl.main(args)
