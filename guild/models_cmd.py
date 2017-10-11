import click

import guild.click_util

@click.command()
@click.option(
    "-p", "--project", "project_location",
    help="Project location (file system directory) for models.",
    metavar="LOCATION")
# TODO: add system option to show models system wide
@click.option(
    "-v", "--verbose",
    help="Show model details.",
    is_flag=True)

@click.pass_context
@guild.click_util.use_args

def models(ctx, args):
    """Show available models.

    By default Guild will show models defined in the current directory
    (in a MODEL or MODELS file). You may use --project to specify an
    alternative project location.

    To show installed models, use the --installed option. Any location
    specified by --project, will be ignored if --installed is used.
    """
    import guild.models_cmd_impl
    guild.models_cmd_impl.main(args, ctx)
