import os

import guild.cli
import guild.project

DEFAULT_PROJECT_LOCATION = "."

def main(args):
    location = args.project_location or DEFAULT_PROJECT_LOCATION
    try:
        project = guild.project.from_file_or_dir(location)
    except (guild.project.MissingSourceError, IOError):
        _no_such_project_error(args)
    else:
        guild.cli.table(
            [_format_op(op) for op in _iter_ops(project, args)],
            cols=["full_name", "description"],
            detail=(["cmd"] if args.verbose else []))

def _no_such_project_error(args):
    if not args.project_location:
        guild.cli.error(
            "the current directory does not contain a MODEL (or MODELS) file\n"
            "Try specifying a project location or "
            "'guild operations --help' for more information.")
    else:
        guild.cli.error(
            "'%s' does not contain a MODEL (or MODELS) file\n"
            "Try a different location or 'guild operations --help' "
            "for more information."
            % args.project_location)

def _iter_ops(project, args):
    for model in _project_models(project, args):
        for op in model.operations:
            yield op

def _project_models(project, args):
    if args.model:
        return [_try_model(args.model, project)]
    else:
        return list(project)

def _try_model(name, project):
    try:
        return project[name]
    except KeyError:
        _no_such_model_error(name, project)

def _no_such_model_error(name, project):
    guild.cli.error(
        "model '%s' is not defined in %s\n"
        "Try 'guild models%s' for a list of models."
        % (name, os.path.relpath(project.src),
           _project_opt(project.src)))

def _project_opt(project_src):
    relpath = os.path.relpath(project_src)
    if relpath == "MODEL" or relpath == "MODELS":
        return ""
    else:
        return " -p %s" % relpath

def _format_op(op):
    return {
        "name": op.name,
        "model": op.model.name,
        "full_name": "%s:%s" % (op.model.name, op.name),
        "description": op.description,
        "cmd": op.cmd,
    }
