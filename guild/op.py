import os
import shlex

import guild.util

class InvalidCmdSpec(ValueError):
    pass

class Operation(object):

    def __init__(self, cmd_args, cmd_env, cmd_cwd):
        self.cmd_args = cmd_args
        self.cmd_env = cmd_env
        self.cmd_cwd = cmd_cwd

    def run(self):
        print("Run %s and wait" % self.cmd_args)

def from_project_op(project_op):
    cmd_args = _python_cmd_for_project_op(project_op)
    cmd_env = {}
    cmd_cwd = "."
    return Operation(cmd_args, cmd_env, cmd_cwd)

def _python_cmd_for_project_op(project_op):
    spec = project_op.cmd
    spec_parts = shlex.split(spec)
    if len(spec_parts) < 1:
        raise InvalidCmdSpec(spec)
    script = _resolve_script_path(spec_parts[0], project_op.project.src)
    return ["python", "-u", script] + spec_parts[1:]

def _resolve_script_path(script, project_src):
    script_path = _script_path_for_project_src(script, project_src)
    return guild.util.find_apply(
        [_explicit_path,
         _path_missing_py_ext,
         _unmodified_path],
        script_path)

def _script_path_for_project_src(script, project_src):
    project_dir = os.path.dirname(project_src)
    return os.path.join(project_dir, script)

def _explicit_path(path):
    return path if os.path.isfile(path) else None

def _path_missing_py_ext(part_path):
    return _explicit_path(part_path + ".py")

def _unmodified_path(val):
    return val
