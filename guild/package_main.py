# Copyright 2017-2018 TensorHub, Inc.
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

import logging
import os
import sys

import setuptools
import twine.commands.upload
import yaml

import guild.help

from guild import guildfile
from guild import namespace
from guild import pip_util
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
    path = os.environ["PACKAGE_FILE"]
    try:
        gf = guildfile.from_file(path)
    except (IOError, guildfile.GuildfileError) as e:
        _exit("error reading %s\n%s" % (path, e))
    else:
        if not gf.package:
            _exit("%s does not contain a package definition" % path)
        return gf.package

def _create_dist(pkg):
    sys.argv = _bdist_wheel_cmd_args(pkg)
    kw = _setup_kw(pkg)
    _write_package_metadata(pkg, kw)
    return setuptools.setup(**kw)

def _bdist_wheel_cmd_args(pkg):
    args = [sys.argv[0], "bdist_wheel"]
    args.extend(_python_tag_args(pkg))
    args.extend(_dist_dir_args())
    return args

def _python_tag_args(pkg):
    if pkg.python_tag:
        return ["--python-tag", pkg.python_tag]
    else:
        return ["--universal"]

def _dist_dir_args():
    dist_dir = os.getenv("DIST_DIR")
    if dist_dir:
        return ["--dist-dir", dist_dir]
    else:
        return []

def _setup_kw(pkg):
    project_dir = os.path.dirname(pkg.guildfile.src)
    desc, long_desc = _pkg_description(pkg)
    return dict(
        name=pkg.name,
        version=pkg.version,
        description=desc,
        long_description=long_desc,
        url=pkg.url,
        author=pkg.author,
        author_email=pkg.author_email,
        license=pkg.license,
        keywords=" ".join(pkg.tags),
        python_requires=_pkg_python_requires(pkg),
        install_requires=_pkg_install_requires(pkg),
        packages=[pkg.name],
        package_dir={pkg.name: project_dir},
        namespace_packages=_namespace_packages(pkg),
        package_data={
            pkg.name: _package_data(pkg)
        },
        entry_points=_entry_points(pkg),
    )

def _pkg_description(pkg):
    """Returns a tuple of the package description and long description.

    The description is the first line of the package description
    field. Long description is generated and consists of subsequent
    lines in the package description, if they exist, plus
    reStructuredText content representing the models and model details
    defined in the package.

    """
    desc_lines = pkg.description.split("\n")
    desc = desc_lines[0]
    long_desc = "\n\n".join(desc_lines[1:])
    pkg_desc = guild.help.package_description(pkg.guildfile)
    long_desc += "\n\n" + pkg_desc
    return desc, long_desc

def _namespace_packages(pkg):
    if pkg.name.startswith("gpkg."):
        return ["gpkg"]
    else:
        return []

def _package_data(pkg):
    return _pkg_data_files(pkg) + _default_pkg_files()

def _pkg_data_files(pkg):
    return pkg.data_files

def _default_pkg_files():
    return [
        "guild.yml",
        "LICENSE",
        "LICENSE.*",
        "README",
        "README.*",
    ]

def _entry_points(pkg):
    return {
        name: eps
        for name, eps in [
                ("guild.models", _model_entry_points(pkg)),
                ("guild.resources", _resource_entry_points(pkg))
        ]
        if eps
    }

def _model_entry_points(pkg):
    return [
        "%s = guild.model:PackageModel" % model.name
        for _name, model in sorted(pkg.guildfile.models.items())
    ]

def _resource_entry_points(pkg):
    return _model_resource_entry_points(pkg)

def _model_resource_entry_points(pkg):
    return [
        ("%s:%s = guild.model:PackageModelResource"
         % (resdef.modeldef.name, resdef.name))
        for resdef in _iter_guildfile_resdefs(pkg)
    ]

def _iter_guildfile_resdefs(pkg):
    for modeldef in pkg.guildfile.models.values():
        for resdef in modeldef.resources:
            yield resdef

def _pkg_python_requires(pkg):
    return ", ".join(pkg.python_requires)

def _pkg_install_requires(pkg):
    if pkg.requires is None:
        return _maybe_requirements_txt(pkg)
    return [_project_name(req) for req in pkg.requires]

def _maybe_requirements_txt(pkg):
    requirements_txt = os.path.join(pkg.guildfile.dir, "requirements.txt")
    if not os.path.exists(requirements_txt):
        return []
    return _parse_requirements(requirements_txt)

def _parse_requirements(path):
    parsed = pip_util.parse_requirements(path)
    return [str(req.req) for req in parsed]

def _project_name(req):
    ns, project_name = namespace.split_name(req)
    pip_info = ns.pip_info(project_name)
    return pip_info.project_name

def _write_package_metadata(pkg, setup_kw):
    egg_info_dir = "%s.egg-info" % setup_kw["name"]
    util.ensure_dir(egg_info_dir)
    dest = os.path.join(egg_info_dir, "PACKAGE")
    with open(dest, "w") as f:
        yaml.dump(_pkg_metadata(pkg), f, default_flow_style=False, width=9999)

def _pkg_metadata(pkg):
    for item in pkg.guildfile.data:
        if "package" in item:
            return item
    raise AssertionError(pkg.data)

def _maybe_upload(dist):
    upload_repo = os.getenv("UPLOAD_REPO")
    if upload_repo:
        _upload(dist, upload_repo)

def _upload(dist, upload_repo):
    _check_wheel_metadata_version(dist)
    args = _twine_upload_args(dist, upload_repo)
    try:
        twine.commands.upload.main(args)
    except Exception as e:
        _handle_twine_error(e)

def _check_wheel_metadata_version(dist):
    """Confirm that metadata generated by wheel is supported by pkginfo.

    Version 0.31.0 of the wheel package started using metadata version
    2.1, which is not supported by versions of pkginfo earlier than
    1.4.2. Upgrading wheel without upgrading pkginfo will leave the
    env unable to read pkg info generated in wheels. Utils like twine
    rely on this and will break.

    This is a check to confirm that the metadata generated by wheel
    can be read using pkginfo.

    """
    from pkginfo import distribution
    from wheel import metadata
    egg_info_path = dist.get_name() + ".egg-info"
    pkginfo_path = os.path.join(egg_info_path, "PKG-INFO")
    msg = metadata.pkginfo_to_metadata(egg_info_path, pkginfo_path)
    metadata_ver = msg["Metadata-Version"]
    supported_vers = distribution.HEADER_ATTRS.keys()
    if metadata_ver not in supported_vers:
        raise AssertionError(
            "wheel metadata version '%s' is not supported by pkginfo "
            "(should be one of %s)\n"
            "Try upgrading pkginfo to the latest version."
            % (metadata_ver, ", ".join(map(repr, supported_vers))))

def _twine_upload_args(dist, repo):
    args = []
    args.extend(_twine_repo_args(repo))
    args.extend(_twine_sign_args())
    args.extend(_twine_dist_file_args(dist))
    if os.getenv("SKIP_EXISTING"):
        args.append("--skip-existing")
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
    if os.getenv("DEBUG"):
        logging.exception("twine error")
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
