import guild.cli
import guild.config

def list(_args):
    import pandas
    sources = pandas.DataFrame(guild.config.sources())
    sources.sort_values("name")
    guild.cli.out(sources.to_string(index=False, header=False))

def add(args):
    print("TODO: add source %s" % args)
