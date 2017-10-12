import os

import guild.cli
import guild.click_util
import guild.package
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
    msg_parts.append(try_project_location_help(location, cmd_ctx))
    guild.cli.error("".join(msg_parts))

def project_location_desc(location):
    location = project_location_option(location)
    return ("%s" % location if location
            else "the current directory")

def try_project_location_help(location, cmd_ctx=None):
    location = project_location_option(location)
    help_parts = []
    if location:
        help_parts.append("Try specifying a different location")
    else:
         help_parts.append("Try specifying a project location")
    if cmd_ctx:
        help_parts.append(
            " or '%s' for more information."
            % guild.click_util.ctx_cmd_help(cmd_ctx))
    else:
        help_parts.append(".")
    return "".join(help_parts)

def project_location_option(location):
    location = os.path.abspath(location or "")
    basename = os.path.basename(location)
    if basename in ["MODEL", "MODELS", "__generated__"]:
        location = os.path.dirname(location)
    if location == os.getcwd():
        return ""
    else:
        return location

def split_pkg(pkg):
    try:
        return guild.package.split_name(pkg)
    except guild.namespace.NamespaceError as e:
        namespaces = ", ".join(
            [name for name, _ in guild.namespace.iter_namespaces()])
        guild.cli.error(
        "unknown namespace '%s' in %s\n"
        "Supported namespaces: %s"
        % (e.value, pkg, namespaces))
