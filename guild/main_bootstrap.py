import os
import sys

EXTERNAL_PATHS = [
    "org_click",
    "org_html5lib",
    "org_mozilla_bleach",
    "org_psutil",
    "org_pythonhosted_markdown",
    "org_tensorflow_tensorboard",
    "protobuf/python",
]

def main():
    sys.path[:0] = _external_import_paths()
    _check_requires()
    import guild.main
    guild.main.main()

def _external_import_paths():
    external_root = _external_root()
    return [
        _external_import_path(path, external_root)
        for path in EXTERNAL_PATHS
    ]

def _external_root():
    root = _package_external_dir() or _bazel_runfiles_dir()
    assert root, "could not find external root"
    return root

def _package_external_dir():
    guild_pkg_dir = os.path.dirname(__file__)
    external_dir = os.path.join(guild_pkg_dir, "external")
    return external_dir if os.path.exists(external_dir) else None

def _bazel_runfiles_dir():
    script_dir = os.path.dirname(sys.argv[0])
    runfiles_dir = os.path.join(script_dir, "guild.runfiles")
    return runfiles_dir if os.path.exists(runfiles_dir) else None

def _external_import_path(path, root):
    if isinstance(path, tuple):
        if sys.version_info[0] == 2:
            path = path[0]
        else:
            path = path[1]
    return os.path.join(root, path)

def _check_requires():
    import pkg_resources
    import guild
    try:
        pkg_resources.require(*guild.__requires__)
    except pkg_resources.DistributionNotFound as e:
        _handle_missing_req(e.req)

def _handle_missing_req(req):
    msg_parts = ["guild: missing required package '%s'\n" % req]
    if req.project_name == "pip":
        msg_parts.append(
            "Refer to https://pip.pypa.io/en/stable/installing "
            "for more information.")
    else:
        msg_parts.append("Try 'pip install %s' to install the package." % req)
    sys.stderr.write("".join(msg_parts))
    sys.stderr.write("\n")
    sys.exit(1)
