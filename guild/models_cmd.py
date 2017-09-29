import guild.cli
import guild.project

DEFAULT_PROJECT_LOCATION = "."

def main(args):
    if args.installed:
        _maybe_ignore_project(args)
        _print_installed_models()
    else:
        _print_project_models(args)

def _maybe_ignore_project(args):
    if args.project_location:
        guild.cli.out(
            "Ignoring models in '%s' because --installed was specified."
            % args.project_location,
            err=True)

def _print_installed_models():
    print("TODO: print installed models")

def _print_project_models(args):
    location = args.project_location or DEFAULT_PROJECT_LOCATION
    try:
        project = guild.project.from_file_or_dir(location)
    except (guild.project.MissingSourceError, IOError):
        _no_such_project_error(args)
    else:
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
        "description": model.description,
        "operations": ", ".join([op.name for op in model.operations])
    }

def _no_such_project_error(args):
    if not args.project_location:
        guild.cli.error(
            "current directory does not contain any models\n"
            "Try specifying a project location or "
            "'guild models --help' for more information.")
    else:
        guild.cli.error(
            "'%s' does not contain any models\n"
            "Try a different location or 'guild models --help' "
            "for more information."
            % args.project_location)
