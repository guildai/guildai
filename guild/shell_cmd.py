import click

import guild.click_util

@click.command()

@guild.click_util.use_args

def shell(args):
    """Start a Python shell for API experimentation.
    """
    import guild.shell_cmd_impl
    guild.shell_cmd_impl.main(args)
