import click

import guild.app
import guild.cli

guild.app.init()

###################################################################
# Main
###################################################################

@click.group()
@click.version_option(
    version=guild.app.version(),
    prog_name="guild",
    message="%(prog)s %(version)s"
)
@click.option("--debug", hidden=True, is_flag=True)

def cli(**kw):
    """Guild AI command line interface."""
    guild.cli.main(**kw)

def main():
    guild.cli.apply_main(cli)

class Args(object):

    def __init__(self, kw):
        for name in kw:
            setattr(self, name, kw[name])

def project_options(flag_support=False):
    # pylint: disable=protected-access
    def decorator(f):
        if flag_support:
            click.decorators._param_memo(f, click.Option(
                ["flags", "-F", "--flag"],
                help="Define a project flag; may be used multiple times.",
                multiple=True,
                metavar="NAME[=VAL]"))
            click.decorators._param_memo(f, click.Option(
                ["profiles", "-p", "--profile"],
                help="Use alternate flags profile.",
                multiple=True,
                metavar="NAME"))
        click.decorators._param_memo(f, click.Option(
            ["project_dir", "-P", "--project"],
            help="Project directory (default is current directory).",
            metavar="DIR",
            default="."))
        return f
    return decorator

def preview_option():
    # pylint: disable=protected-access
    def decorator(f):
        click.decorators._param_memo(f, click.Option(
            ["--preview"],
            help="Show operation details but do not perform the operation.",
            is_flag=True))
        return f
    return decorator

###################################################################
# Check command
###################################################################

@click.command(short_help="Check Guild setup and run tests.")
@click.option(
    "-T", "--tests", "all_tests",
    help="Run Guild test suite.",
    is_flag=True)
@click.option(
    "-t", "--test", "tests",
    help="Run TEST (may be used multiple times).",
    metavar="TEST",
    multiple=True)
@click.option(
    "-s", "--skip-info",
    help="Don't print info (useful when just running tests).",
    is_flag=True)
@click.option(
    "-v", "--verbose",
    help="Show check details.",
    is_flag=True)

def check(**kw):
    """Checks Guild setup.

    This command performs a number of checks and prints information
    about the Guild setup.

    You can also run the Guild test suite by specifying the --tests
    option.
    """
    import guild.check_cmd
    guild.check_cmd.main(Args(kw))

cli.add_command(check)
