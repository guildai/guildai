import glob
import os
import sys

import setuptools
import yaml

class Pkg(object):

    def __init__(self, src, data):
        self.src = src
        self.data = data

    def __getitem__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            _exit(
                "%s is missing required '%s' attribute"
                % (self.src, attr))

    def get(self, attr, default=None):
        return self.data.get(attr, default)

def main():
    pkg_file = os.getenv("PACKAGE_FILE")
    pkg = _load_pkg(pkg_file)
    sys.argv = _bdist_wheel_cmd_args(pkg)
    setuptools.setup(**_setup_kw(pkg))

def _load_pkg(path):
    try:
        f = open(path, "r")
    except IOError as e:
        _exit("error reading %s\n%s" % (path, e))
    else:
        try:
            data = yaml.load(f)
        except yaml.YAMLError as e:
            _exit("error reading %s\n%s" % (path, e))
        else:
            return Pkg(path, data)

def _bdist_wheel_cmd_args(pkg):
    args = [sys.argv[0], "bdist_wheel"]
    args.extend(_python_tag_args(pkg))
    args.extend(_dist_dir_args())
    return args

def _python_tag_args(pkg):
    tag = pkg.get("python-tag")
    if tag:
        return ["--python-tag", tag]
    else:
        return ["--universal"]

def _dist_dir_args():
    dist_dir = os.getenv("DIST_DIR")
    if dist_dir:
        return ["--dist-dir", dist_dir]
    else:
        return []

def _setup_kw(pkg):
    pkg_name = "gpkg." + pkg["name"]
    project_dir = os.path.dirname(pkg.src)
    desc, long_desc = _parse_description(pkg)
    return dict(
        name=pkg_name,
        version=pkg["version"],
        description=desc,
        long_description=long_desc,
        url=pkg["url"],
        maintainer=pkg.get("maintainer"),
        maintainer_email=pkg["maintainer-email"],
        license=pkg.get("license"),
        keywords=" ".join(pkg.get("tags", [])),
        python_requires=", ".join(pkg.get("python-requires", [])),
        packages=[pkg_name],
        package_dir={pkg_name: project_dir},
        namespace_packages=["gpkg"],
        package_data={
            pkg_name: _package_data(pkg)
        }
    )

def _parse_description(pkg):
    desc = pkg.get("description", "").strip()
    lines = desc.split("\n")
    return lines[0], "\n\n".join(lines[1:])

def _package_data(pkg):
    user_defined = pkg.get("data")
    return (user_defined if user_defined
            else _default_package_data(pkg))

def _default_package_data(pkg):
    return [
        "MODEL",
        "MODELS",
        "LICENSE",
        "LICENSE.*",
        "README",
        "README.*",
    ]

def _exit(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
