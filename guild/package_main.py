# Copyright 2017-2019 TensorHub, Inc.
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

import glob
import logging
import os
import sys

import setuptools
import six
import twine.commands.upload
import yaml

import guild.help

from guild import guildfile
from guild import namespace
from guild import pip_util
from guild import util

MULTI_ARCH_PACKAGES = ("tensorflow-any",)

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
            return _default_package(gf)
        else:
            return gf.package

def _default_package(gf):
    # Use the name of the default model
    default_model = gf.default_model
    package_name = (
        default_model.name if (default_model and default_model.name)
        else "package")
    return guildfile.PackageDef(package_name, {}, gf)

def _create_dist(pkg):
    sys.argv = _bdist_wheel_cmd_args(pkg)
    kw = _setup_kw(pkg)
    _maybe_print_kw_and_exit(kw)
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
    summary, help_desc = _pkg_description(pkg)
    project_name = pkg.name
    python_pkg_name = _python_pkg_name(pkg)
    packages, package_dir = _python_packages(
        pkg, python_pkg_name, project_dir)
    return dict(
        name=project_name,
        version=pkg.version,
        description=summary,
        long_description=help_desc,
        url=pkg.url,
        author=pkg.author,
        author_email=pkg.author_email,
        license=pkg.license,
        keywords=_pkg_keywords(pkg),
        python_requires=pkg.python_requires,
        install_requires=_pkg_install_requires(pkg),
        packages=packages,
        package_dir=package_dir,
        namespace_packages=_namespace_packages(python_pkg_name),
        package_data={
            python_pkg_name: _package_data(pkg)
        },
        entry_points=_entry_points(pkg),
    )

def _pkg_description(pkg):
    """Returns a tuple of the package summary and long description.

    The summary is the first line of the package description
    field. Long description is generated using Guild's help generafor
    the package description (restructured text format).

    """
    pkg_desc_lines = pkg.description.split("\n")
    summary = pkg_desc_lines[0]
    help_desc = guild.help.package_description(pkg.guildfile)
    return summary, help_desc

def _python_pkg_name(pkg):
    return pkg.name.replace("-", "_")

def _python_packages(pkg, base_pkg, project_dir):
    if pkg.packages is not None:
        return (
            pkg.packages.keys(),
            pkg.packages
        )
    return _default_python_packages(base_pkg, project_dir)

def _default_python_packages(base_pkg, project_dir):
    found_pkgs = setuptools.find_packages()
    all_pkgs = [base_pkg] + _apply_base_pkg(base_pkg, found_pkgs)
    pkg_dirs = _all_pkg_dirs(project_dir, base_pkg, found_pkgs)
    return all_pkgs, pkg_dirs

def _apply_base_pkg(base_pkg, found_pkgs):
    return ["%s.%s" % (base_pkg, pkg) for pkg in found_pkgs]

def _all_pkg_dirs(project_dir, base_pkg, found_pkgs):
    pkg_dirs = {
        base_pkg: project_dir
    }
    pkg_dirs.update({
        found_pkg: os.path.join(
            project_dir,
            found_pkg.replace(".", os.path.sep))
        for found_pkg in found_pkgs
    })
    return pkg_dirs

def _namespace_packages(python_pkg_name):
    parts = python_pkg_name.rsplit(".", 1)
    if len(parts) == 1:
        return []
    else:
        return [parts[0]]

def _package_data(pkg):
    return _pkg_data_files(pkg) + _default_pkg_files()

def _pkg_data_files(pkg):
    matches = []
    for pattern in pkg.data_files:
        matches.extend(glob.glob(pattern))
    return matches

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
        ] if eps
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

def _pkg_keywords(pkg):
    tags = list(pkg.tags)
    if "gpkg" not in tags:
        tags.append("gpkg")
    return " ".join(tags)

def _pkg_install_requires(pkg):
    if not pkg.requires:
        return _maybe_requirements_txt(pkg)
    return [
        _project_name(req)
        for req in pkg.requires
        if not _is_multi_arch_req(req)]

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

def _is_multi_arch_req(req):
    for multi_arch_pkg in MULTI_ARCH_PACKAGES:
        if req.startswith(multi_arch_pkg):
            return True
    return False

def _maybe_print_kw_and_exit(kw):
    if os.getenv("DUMP_SETUP_KW") == "1":
        import pprint
        pprint.pprint(kw)
        sys.exit(0)

def _write_package_metadata(pkg, setup_kw):
    egg_info_dir = "%s.egg-info" % setup_kw["name"]
    util.ensure_dir(egg_info_dir)
    dest = os.path.join(egg_info_dir, "PACKAGE")
    with open(dest, "w") as f:
        yaml.dump(_pkg_metadata(pkg), f, default_flow_style=False, width=9999)

def _pkg_metadata(pkg):
    for item in pkg.guildfile.data:
        if "package" in item:
            return _coerce_pkg_data(item)
    return {}

def _coerce_pkg_data(data):
    return {
        attr: _coerce_pkg_attr(attr, val)
        for attr, val in data.items()
    }

def _coerce_pkg_attr(name, val):
    if name == "requires" and isinstance(val, six.string_types):
        return [val]
    return val

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
