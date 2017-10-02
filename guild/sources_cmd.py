import guild.cli
import guild.config

def list_sources(_args):
    sources = guild.config.sources()
    guild.cli.table(sources, ["name", "source"])

def add(args):
    try:
        guild.config.add_source(args.name, args.source)
    except guild.config.SourceExistsError:
        guild.cli.error("source '%s' already exists" % args.name)

def remove(args):
    try:
        guild.config.remove_source(args.name)
    except guild.config.SourceNameError:
        guild.cli.error("source '%s' does not exist" % args.name)
