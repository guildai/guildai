import guild.cli
import guild.project

DEFAULT_PROJECT_LOCATION = "."

def main(args):
    model_name, op_name = _parse_opspec(args.opspec)
    model = _resolve_model(model_name, args)
    op = _resolve_op(op_name, model)
    print("TODO: run %s on %s" % (op, model))

def _parse_opspec(spec):
    parts = spec.split(":", 1)
    if len(parts) == 1:
        return None, parts[0]
    else:
        return parts

def _resolve_model(name, args):
    project = _project_for_args(args)
    if name is None:
        if project is None:
            _project_required_error()
        return _project_default_model(project)
    elif project is not None:
        return _project_model(name, project)
    else:
        package = _package_for_args(args)
        if package is None:
            _package_not_installed_error(package)
        return _package_model(name, package)

def _project_for_args(args):
    location = args.project_location or DEFAULT_PROJECT_LOCATION
    try:
        return guild.project.from_file_or_dir(location)
    except guild.project.MissingSourceError:
        if args.project_location:
            _missing_source_error(args.project_location)
        return None

def _missing_source_error(location):
    guild.cli.error(
        "'%s' does not contain a MODEL (or MODELS) file\n"
        "Try a different location or 'guild run --help' "
        "for more information."
        % location)

def _project_required_error():
    guild.cli.error(
        "cannot find a model for this operation\n"
        "Try specifying a project, a package or 'guild run --help' "
        "for more information.")

def _project_default_model(project):
    default = project.default_model()
    if default:
        return default
    else:
        _no_models_for_project_error(project)

def _no_models_for_project_error(project):
    guild.cli.error("%s does not define any models" % project.src)

def _project_model(name, project):
    try:
        return project[name]
    except KeyError:
        _no_such_model_error(name, project)

def _no_such_model_error(name, project):
    guild.cli.error(
        "model '%s' is not defined in %s\n"
        "Try 'guild models%s' for a list of available models."
        % (name, project.src, _project_opt(project.src)))

def _project_opt(model_src):
    if model_src == "./MODEL" or model_src == "./MODELS":
        return ""
    else:
        return " -p %s" % model_src

def _package_for_args(_args):
    # TODO: package resolve here!
    return None

def _package_not_installed_error(name):
    guild.cli.error(
        "package '%s' is not installed\n"
        "Try 'guild install %s' to install it first."
        % name)

def _package_model(name, package):
    raise AssertionError("TODO")

def _resolve_op(name, model):
    op = model.get_op(name)
    if op is None:
        _no_such_operation_error(name, model)
    return op

def _no_such_operation_error(name, model):
    guild.cli.error(
        "operation '%s' is not defined for model '%s'\n"
        "Try 'guild operations %s%s' for a list of available operations."
        % (name, model.name, model.name, _project_opt(model.project.src)))
