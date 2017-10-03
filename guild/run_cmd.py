import os

import guild.cli
import guild.op
import guild.project

DEFAULT_PROJECT_LOCATION = "."

def main(args):
    model_name, op_name = _parse_opspec(args.opspec)
    model = _resolve_model(model_name, args)
    project_op = _resolve_op(op_name, model)
    _apply_flags(args, project_op)
    op = guild.op.from_project_op(project_op)
    if args.yes or _confirm_op(op):
        result = op.run()
        _handle_run_result(result)

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
        "'%s' does not contain any models\n"
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

def _project_opt(project_src):
    relpath = os.path.relpath(project_src)
    if relpath == "MODEL" or relpath == "MODELS":
        return ""
    else:
        return " -p %s" % relpath

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

def _apply_flags(args, op):
    for arg in args.args:
        name, val = _parse_flag(arg)
        op.flags[name] = val

def _parse_flag(s):
    parts = s.split("=", 1)
    if len(parts) == 1:
        return parts[0], None
    else:
        return parts

def _confirm_op(op):
    flags = _op_flags(op)
    if flags:
        prompt = (
            "You are about to run %s with the following flags:\n"
            "%s\n"
            "Continue?"
            % (op.name, _format_op_flags(flags)))
    else:
        prompt = (
            "You are about to run %s:\n"
            "Continue?" % op.name)
    return guild.cli.confirm(prompt, default=True)

def _op_flags(op):
    flags = []
    args = op.cmd_args
    i = 1
    while i < len(args):
        cur_arg = args[i]
        i = i + 1
        next_arg = args[i] if i < len(args) else None
        if cur_arg[0:2] == "--":
            if next_arg and next_arg[0:2] != "--":
                flags.append((cur_arg[2:], next_arg))
                i = i + 1
            else:
                flags.append((cur_arg[2:], None))
    return flags

def _format_op_flags(flags):
    return "\n".join(["  %s" % _format_flag(name, val)
                      for name, val in flags])

def _format_flag(name, val):
    if val is None:
        return "%s: (boolean switch)" % name
    else:
        return "%s: %s" % (name, val)

def _handle_run_result(exit_status):
    if exit_status != 0:
        guild.cli.error(exit_status=exit_status)
