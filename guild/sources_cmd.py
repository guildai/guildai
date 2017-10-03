import guild.cli
import guild.config

def list_sources(_args):
    sources = guild.config.sources()
    guild.cli.table(sources, ["name", "source"])

def add_source(args, ctx):
    try:
        guild.config.add_source(args.name, args.source)
    except guild.config.SourceExistsError:
        guild.cli.error(
            "source '%s' already exists\n"
            "Try a different name or '%s' for more information."
            % (args.name, cli.ctx_cmd_help(ctx)))

def remove_source(args):
    try:
        guild.config.remove_source(args.name)
    except guild.config.SourceNameError:
        guild.cli.error(
            "source '%s' does not exist\n"
            "Try 'guild sources' for a list."
            % args.name)
