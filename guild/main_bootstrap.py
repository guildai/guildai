import os
import sys

EXTERNAL_PATHS = [
    "org_click",
    "org_html5lib",
    "org_mozilla_bleach",
    "org_pip/src",
    "org_pocoo_werkzeug",
    "org_psutil",
    "org_pythonhosted_markdown",
    ("org_pyyaml/lib", "org_pyyaml/lib3"),
    "org_setuptools",
    "org_tensorflow_tensorboard",
    "protobuf/python",
]

def main():
    sys.path[:0] = _external_import_paths()
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
