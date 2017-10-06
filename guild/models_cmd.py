import guild.cli
import guild.cmd_support

def main(args, ctx):
    if args.installed:
        _maybe_ignore_project(args)
        _print_installed_models()
    else:
        _print_project_models(args, ctx)

def _maybe_ignore_project(args):
    if args.project_location:
        guild.cli.out(
            "Ignoring models in '%s' because --installed was specified."
            % args.project_location,
            err=True)

def _print_installed_models():
    print("TODO: print installed models")

def _print_project_models(args, ctx):
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
