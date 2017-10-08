import guild.cli
import guild.cmd_support

def main(args, ctx):
    project = guild.cmd_support.project_for_location(
        args.project_location, ctx)
    guild.cli.table(
        [_format_model(model) for model in project],
        cols=["name", "description"],
        detail=(["source", "version", "operations"]
                if args.verbose else []))

def _format_model(model):
    return {
        "source": model.project.src,
        "name": model.name,
        "version": model.version,
        "description": model.description or "",
        "operations": ", ".join([op.name for op in model.operations])
    }
