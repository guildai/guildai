import guild.cli
import guild.project

DEFAULT_PROJECT_LOCATION = "."

def main(args):
    if args.installed:
        _maybe_ignore_project_or_package(args)
        _print_installed_models()
    else:
        _print_project_or_package_models(args)

def _maybe_ignore_project_or_package(args):
    if args.project_or_package:
        guild.cli.out(
            "Ignoring models defined in '%s' because "
            "the --installed option was specified"
            % args.project_or_package,
            err=True)

def _print_installed_models():
    print("TODO: print installed models")

def _print_project_or_package_models(args):
    try:
        _print_project_models(args)
    except (guild.project.MissingSourceError, IOError):
        try:
            _print_package_models(args)
        except Exception:
            _no_such_project_or_package_error(args)

def _print_project_models(args):
    location = args.project_or_package or DEFAULT_PROJECT_LOCATION
    project = guild.project.from_file_or_dir(location)
    guild.cli.table(
        [_format_model(model) for model in project],
        cols=["name", "description"],
        detail=["source", "version", "operations"] if args.verbose else [])

def _format_model(model):
    return {
        "source": model.project.src,
        "name": model.name,
        "version": model.version,
        "description": model.description,
        "operations": ", ".join([op.name for op in model.operations])
    }

def _print_package_models(args):
    # TODO: lookup installed
    raise AssertionError()

def _no_such_project_or_package_error(args):
    if not args.project_or_package:
        guild.cli.error(
            "current directory does not contain any models\n"
            "Try specifying a project location, a package or "
            "'guild models --help' for more information.")
    elif _is_path(args.project_or_package):
        guild.cli.error(
            "'%s' does not contain any models\n"
            "Try a different location or 'guild models --help' "
            "for more information."
            % args.project_or_package)
    else:
        guild.cli.error(
            "cannot find package '%s'\n"
            "Try 'guild models --installed' to list installed models."
            % args.project_or_package)

def _is_path(s):
    return s and s[0] in "./\\"
