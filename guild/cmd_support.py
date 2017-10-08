import os

import guild.cli
import guild.project
import guild.util

class NoProject(Exception):
    pass

def project_for_location(location, cmd_ctx=None):
    project = find_project_for_location(location)
    if project is None:
        _no_project_error(location, cmd_ctx)
    return project

def find_project_for_location(location):
    location = location or "."
    try:
        return _project_for_location(location)
    except NoProject:
        return None

def _project_for_location(location):
    try:
        return guild.project.from_file_or_dir(location)
    except (guild.project.NoModels, IOError):
        raise NoProject()

def _no_project_error(location, cmd_ctx):
    location = project_location_option(location) or "."
    msg_parts = []
    if os.path.exists(location):
        msg_parts.append(
            "%s does not contain any models\n"
            % project_location_desc(location))
    else:
        msg_parts.append("%s does not exist\n" % location)
    if location:
        msg_parts.append("Try specifying a different location")
    else:
         msg_parts.append("Try specifying a project location")
    if cmd_ctx:
        msg_parts.append(
            " or '%s' for more information."
            % guild.cli.ctx_cmd_help(cmd_ctx))
    else:
        msg_parts.append(".")
    guild.cli.error("".join(msg_parts))

def project_location_desc(location):
    location = project_location_option(location)
    return ("%s" % location if location
            else "the current directory")

def project_location_option(location):
    location = os.path.abspath(location or "")
    basename = os.path.basename(location)
    if basename in ["MODEL", "MODELS", "__generated__"]:
        location = os.path.dirname(location)
    if location == os.getcwd():
        return ""
    else:
        return location
