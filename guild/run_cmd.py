import guild.cli

def main(args):
    model_name, op_name = _parse_opspec(args.opspec)
    model = _resolve_model_name(model_name, args)
    print("TODO: run %s on %s" % (op_name, model))

def _parse_opspec(spec):
    parts = spec.split(":", 1)
    if len(parts) == 1:
        return None, parts[0]
    else:
        return parts

def _resolve_model_name(name, args):
    project = _project_for_args(args)
    if name is None:
        if project is None:
            _project_required_error()
        return _project_default_model(project)
    else:
        pass

def _project_for_args(_args):
    return None

def _project_required_error():
    guild.cli.error(
        "cannot find a project and MODEL was not specified\n"
        "Try 'guild run --help' for additional information.")

def _project_default_model(project):
    pass
