# Copyright 2017 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division

import os
import sys

import setuptools
import yaml
import twine.commands.upload

import guild.help
from guild import modelfile
from guild import util

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
    pkg = _load_pkg()
    dist = _create_dist(pkg)
    _maybe_upload(dist)

def _load_pkg():
    path = os.getenv("PACKAGE_FILE")
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

def _create_dist(pkg):
    sys.argv = _bdist_wheel_cmd_args(pkg)
    return setuptools.setup(**_setup_kw(pkg))

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
    models = _pkg_models(pkg)
    desc, long_desc = _pkg_description(pkg, models)
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
        },
        entry_points={
            "guild.models": [
                "%s = guild.model:Model" % model.name
                for model in _pkg_models(pkg)
            ]
        }
    )

def _pkg_models(pkg):
    pkg_dir = os.path.dirname(pkg.src)
    try:
        return modelfile.from_dir(pkg_dir)
    except modelfile.NoModels:
        _handle_no_models(pkg_dir)

def _handle_no_models(path):
    _exit("PACKAGE directory %s does not contain any models" % path)

def _pkg_description(pkg, models):
    """Returns a tuple of the package description and long description.

    The description is the first line of the PACKAGE description
    field. Long description is generated and consists of subsequent
    lines in the PACKAGE description, if they exist, plus
    reStructuredText content representing the models and model details
    defined in the package.
    """
    desc_lines = pkg.get("description", "").strip().split("\n")
    desc = desc_lines[0]
    long_desc = "\n\n".join(desc_lines[1:])
    refs = [
        ("Modelfile", pkg.get("modelfile", "UNKNOWN")),
    ]
    models_desc = guild.help.package_description(models, refs)
    return desc, "\n\n".join([long_desc, models_desc])

def _package_data(pkg):
    user_defined = pkg.get("data")
    return (
        user_defined if user_defined
        else _default_package_data(pkg))

def _default_package_data(_pkg):
    return [
        "MODEL",
        "MODELS",
        "LICENSE",
        "LICENSE.*",
        "README",
        "README.*",
    ]

def _maybe_upload(dist):
    upload_repo = os.getenv("UPLOAD_REPO")
    if upload_repo:
        _upload(dist, upload_repo)

def _upload(dist, upload_repo):
    args = _twine_upload_args(dist, upload_repo)
    try:
        twine.commands.upload.main(args)
    except Exception as e:
        _handle_twine_error(e)

def _twine_upload_args(dist, repo):
    args = []
    args.extend(_repo_args(repo))
    args.extend(_dist_file_args(dist))
    return args

def _repo_args(repo):
    if guild.parse_url(repo).scheme:
        rc_section = _pypirc_section_for_repo(repo)
        if rc_section:
            return ["--repository", rc_section]
        else:
            return ["--repository-url", repo]
    else:
        return ["--repository", repo]

def _pypirc_section_for_repo(repo):
    config = twine.utils.get_config()
    for section in config:
        if config[section].get("repository") == repo:
            return section
    return None

def _dist_file_args(dist):
    return [df[2] for df in dist.dist_files]

def _handle_twine_error(e):
    try:
        msg = e.message
    except AttributeError:
        msg = str(e)
    _exit(msg)

def _exit(msg, exit_code=1):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
