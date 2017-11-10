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
import shutil
import sys

import setuptools
import yaml
import twine.commands.upload

import guild.help

from guild import namespace
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
    kw = _setup_kw(pkg)
    _write_package_metadata(kw)
    _patch_setuptools_namespaces()
    return setuptools.setup(**kw)

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
        python_requires=_pkg_python_requires(pkg),
        install_requires=_pkg_install_requires(pkg),
        packages=[pkg_name],
        package_dir={pkg_name: project_dir},
        namespace_packages=["gpkg"],
        package_data={
            pkg_name: _package_data(pkg)
        },
        entry_points=_entry_points(pkg),
    )

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
    if models:
        refs = [
            ("Modelfile", pkg.get("modelfile", "UNKNOWN")),
        ]
        long_desc += "\n\n" + guild.help.package_description(models, refs)
    return desc, long_desc

def _package_data(pkg):
    return _pkg_data_files(pkg) + _default_pkg_files()

def _pkg_data_files(pkg):
    return pkg.get("data-files") or []

def _default_pkg_files():
    return [
        "LICENSE",
        "LICENSE.*",
        "MODEL",
        "MODELS",
        "README",
        "README.*",
    ]

def _entry_points(pkg):
    return {
        name: eps
        for name, eps in [
                ("guild.models", _model_eps(pkg)),
                ("guild.resources", _resource_eps(pkg))
        ]
        if eps
    }

def _model_eps(pkg):
    return [
        "%s = guild.model:PackageModel" % model.name
        for model in _pkg_models(pkg)
    ]

def _pkg_models(pkg):
    pkg_dir = os.path.dirname(pkg.src)
    try:
        return modelfile.from_dir(pkg_dir)
    except modelfile.NoModels:
        return []

def _resource_eps(pkg):
    return _model_resource_eps(pkg) + _package_resource_eps(pkg)

def _model_resource_eps(pkg):
    return [
        ("%s:%s = guild.model:PackageModelResource"
         % (resdef.modeldef.name, resdef.name))
        for resdef in _iter_modelfile_resdefs(pkg)
    ]

def _iter_modelfile_resdefs(pkg):
    pkg_dir = os.path.dirname(pkg.src)
    try:
        mf = modelfile.from_dir(pkg_dir)
    except modelfile.NoModels:
        pass
    else:
        for modeldef in mf:
            for resdef in modeldef.resources:
                yield resdef

def _package_resource_eps(pkg):
    return [
        "%s = guild.package:PackageResource" % res_name
        for res_name in pkg.get("resources", {})
    ]

def _pkg_python_requires(pkg):
    return ", ".join(pkg.get("python-requires", []))

def _pkg_install_requires(pkg):
    return [
        _project_name(req)
        for req in pkg.get("requires", [])
    ]

def _project_name(req):
    ns, project_name = namespace.split_name(req)
    pip_info = ns.pip_info(project_name)
    return pip_info.project_name

def _write_package_metadata(setup_kw):
    source = os.getenv("PACKAGE_FILE")
    egg_info_dir = "%s.egg-info" % setup_kw["name"]
    util.ensure_dir(egg_info_dir)
    dest = os.path.join(egg_info_dir, "PACKAGE")
    shutil.copyfile(source, dest)

def _patch_setuptools_namespaces():
    """Prevent creation of *.nspkg.pth entry for packages.

    Guild uses namespaces simply to tuck packages inside a namespace
    and not for real Python package namespaces. The nspkg.pth entry
    created by setuptools can break Python systems in some cases, so
    we disable its creation altogether.

    E.g. https://github.com/pypa/setuptools/issues/805
    """
    from setuptools.namespaces import Installer
    Installer.install_namespaces = lambda *_args: None

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
    args.extend(_twine_repo_args(repo))
    args.extend(_twine_sign_args())
    args.extend(_twine_dist_file_args(dist))
    return args

def _twine_repo_args(repo):
    if util.parse_url(repo).scheme:
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

def _twine_sign_args():
    args = []
    if os.getenv("SIGN"):
        args.append("--sign")
        sign_id = os.getenv("IDENTITY")
        if sign_id:
            args.extend(["--identity", sign_id])
    return args

def _twine_dist_file_args(dist):
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
