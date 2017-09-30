import guild.project
import guild.util

class NoProject(Exception):
    pass

def project_for_location(location, help_on_error=None):
    location = location or "."
    try:
        return _project_for_location(location)
    except NoProject:
        _no_project_error(location, help_on_error)

def _project_for_location(location):
    return guild.util.find_apply(
        [_project_from_file_or_dir,
         _project_from_plugins,
         _raise_no_project],
        location)

def _project_from_file_or_dir(location):
    try:
        return guild.project.from_file_or_dir(location)
    except (guild.project.MissingSourceError, IOError):
        return None

def _project_from_plugins(location):
    return None

def _raise_no_project(_):
    raise NoProject()

def _no_project_error(location, help_on_error):
    msg_parts = []
    if location == ".":
        msg_parts.append("the current directory does not contain any models\n")
        msg_parts.append("Try specifying a project location")
    else:
        msg_parts.append("'%s' does not contain any models\n" % location)
        msg_parts.append("Try specifying a different location")
    if help_on_error:
        msg_parts.append(" or '%s' for more information." % help_on_error)
    else:
        msg_parts.append(".")
    guild.cli.error("".join(msg_parts))
