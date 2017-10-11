import click

import guild.click_util

@click.command()
@click.option(
    "-T", "--tests", "all_tests",
    help="Run Guild test suite.",
    is_flag=True)
@click.option(
    "-t", "--test", "tests", metavar="TEST",
    help="Run TEST (may be used multiple times).",
    multiple=True)
@click.option(
    "-n", "--no-info",
    help="Don't print info (useful when just running tests).",
    is_flag=True)
@click.option(
    "-s", "--skip", metavar="TEST",
    help="Skip TEST when running Guild test suite. Ignored otherwise.",
    multiple=True)
@click.option(
    "-v", "--verbose",
    help="Show check details.",
    is_flag=True)

@guild.click_util.use_args

def check(args):
    """Check the Guild setup.

    This command performs a number of checks and prints information
    about the Guild setup.

    You can also run the Guild test suite by specifying the --tests
    option.
    """
    import guild.check_cmd_impl
    guild.check_cmd_impl.main(args)
