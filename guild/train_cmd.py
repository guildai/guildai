import click

import guild.click_util
import guild.run_cmd

@click.command()
@click.argument("model", required=False)
@guild.run_cmd.run_params

@guild.click_util.use_args

def train(args):
    """Train a model.

    Equivalent to running 'guild run [MODEL:]train [ARG...]'.

    By default MODEL is the default model for project in LOCATION.

    You may omit MODEL (i.e. for training the default model) while
    providing one or more ARG values provided the first ARG value
    contains an equals sign ('='). When specifying a switch (i.e. an
    argument that doesn't accept a value) as the first ARG, you must
    provide MODEL.

    Refer to help for the run command ('guild run --help') for more
    information.

    """
    import guild.run_cmd_impl
    # MODEL is treated as an ARG if it contains an equal sign (see
    # help text above).
    if args.model and "=" in args.model:
        args.args = (args.model,) + args.args
        args.model = None
    args.opspec = "%s:train" % args.model if args.model else "train"
    guild.run_cmd_impl.main(args)
