import guild.cli

def main(args):
    guild.cli.out(
        "run operation %s %s"
        % (args.operation, " ".join(args.args)))
