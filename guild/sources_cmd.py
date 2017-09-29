import guild.cli
import guild.config
import guild.table

def list(_args):
    sources = guild.config.sources()
    guild.table.out(sources, ["name", "url"])

def add(args):
    try:
        guild.config.add_source(args.name, args.url)
    except guild.config.SourceExistsError:
        guild.cli.error("source '%s' already exists" % args.name)

def remove(args):
    try:
        guild.config.remove_source(args.name)
    except guild.config.SourceNameError:
        guild.cli.error("source '%s' does not exist" % args.name)
