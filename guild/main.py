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

###################################################################
# check command
###################################################################

@click.command()
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
    """Check Guild setup and optionally run tests.

    This command performs a number of checks and prints information
    about the Guild setup.

    You can also run the Guild test suite by specifying the --tests
    option.
    """
    import guild.check_cmd
    guild.check_cmd.main(Args(kw))

cli.add_command(check)

###################################################################
# run command
###################################################################

@click.command()
@click.argument("operation", metavar="[MODEL:]OPERATION")
@click.argument("args", metavar="[ARG...]", nargs=-1)

def run(**kw):
    """Run a model operation.
    """
    import guild.run_cmd
    guild.run_cmd.main(Args(kw))

cli.add_command(run)

###################################################################
# runs command
###################################################################

@click.group(invoke_without_command=True)

def runs(**kw):
    """List or manage runs.
    """
    import guild.runs
    guild.runs.list(Args(kw))

cli.add_command(runs)

###################################################################
# runs rm command
###################################################################

@click.command("rm")
@click.argument("runs", metavar="RUN [RUN...]", nargs=-1)

def rm_runs(**kw):
    """Delete one or more runs."""
    import guild.runs
    guild.runs.remove(Args(kw))

runs.add_command(rm_runs)

###################################################################
# shell command
###################################################################

@click.command()

def shell(**kw):
    """Start a Python shell for API experimentation.
    """
    import guild.shell_cmd
    guild.shell_cmd.main(Args(kw))

cli.add_command(shell)

###################################################################
# sources command
###################################################################

@click.group(invoke_without_command=True)

def sources(**kw):
    """List or manage package sources.
    """
    import guild.sources_cmd
    guild.sources_cmd.list(Args(kw))

cli.add_command(sources)

###################################################################
# sources add command
###################################################################

@click.command("add")
@click.argument("name")
@click.argument("url")

def add_source(**kw):
    """Add a package source.

    NAME must be a unique source identifier for this system. Use
    'guild sources' to show a list of configured package sources.

    URL must be a GitHub repository URL or a local directory. GitHub
    repository URLs may be provided in shorthand using
    ACCOUNT/REPOSITORY. For example, the URL 'guildai/guild-packages'
    will be interpreted as
    'https://github.com/guildai/guild-packages'.

    Local directories must be absolute paths. Use a local directory
    will avoid having to sync with an upstream source each time a
    change is made to a package. This is useful for package
    development.
    """
    import guild.sources_cmd
    guild.sources_cmd.add(Args(kw))

sources.add_command(add_source)
