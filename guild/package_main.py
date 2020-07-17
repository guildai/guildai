# Copyright 2017-2020 TensorHub, Inc.
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
import hashlib
import logging
import os
import sys
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    import setuptools

import six
import yaml

from guild import file_util
from guild import guildfile
from guild import help as helplib
from guild import log as loglib
from guild import namespace
from guild import pip_util
from guild import util

log = logging.getLogger("guild")

MULTI_ARCH_PACKAGES = ("tensorflow-any",)


class Pkg(object):
    def __init__(self, src, data):
        self.src = src
        self.data = data

    def __getitem__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            _exit("%s is missing required '%s' attribute" % (self.src, attr))

    def get(self, attr, default=None):
        return self.data.get(attr, default)


def main():
    loglib.init_logging()
    pkgdef = _load_pkgdef()
    dist = _create_dist(pkgdef)
    _maybe_upload(dist)


def _load_pkgdef():
    path = os.environ["PACKAGE_FILE"]
    try:
        gf = guildfile.for_file(path)
    except (IOError, guildfile.GuildfileError) as e:
        _exit("error reading %s\n%s" % (path, e))
    else:
        if not gf.package:
            return _default_pkgdef(gf)
        else:
            return gf.package


def _default_pkgdef(gf):
    # Use the name of the default model
    package_name = _default_package_name(gf)
    return guildfile.PackageDef(package_name, {}, gf)


def _default_package_name(gf):
    default_model = gf.default_model
    if default_model and default_model.name:
        return default_model.name
    return _anonymous_package_name(gf)


def _anonymous_package_name(gf):
    name = "gpkg.anonymous_%s" % _gf_digest(gf)
    log.warning("package name not defined in %s - using %s", gf.src, name)
    return name


def _gf_digest(gf):
    path = os.path.abspath(gf.src)
    return hashlib.md5(path.encode()).hexdigest()[:8]


def _create_dist(pkgdef):
    kw = _setup_kw(pkgdef)
    _maybe_print_kw_and_exit(kw)
    _write_package_metadata(pkgdef, kw)
    if os.getenv("CLEAN_SETUP") == "1":
        _setup_clean(kw)
    return _setup_bdist_wheel(pkgdef, kw)


def _setup_clean(kw):
    with util.SysArgv(_clean_cmd_args()):
        setuptools.setup(**kw)


def _clean_cmd_args():
    return ["clean", "--all"]


def _setup_bdist_wheel(pkgdef, kw):
    with util.SysArgv(_bdist_wheel_cmd_args(pkgdef)):
        return setuptools.setup(**kw)


def _bdist_wheel_cmd_args(pkgdef):
    args = ["bdist_wheel"]
    args.extend(_python_tag_args(pkgdef))
    args.extend(_dist_dir_args())
    return args


def _python_tag_args(pkgdef):
    if pkgdef.python_tag:
        return ["--python-tag", pkgdef.python_tag]
    else:
        return ["--universal"]


def _dist_dir_args():
    dist_dir = os.getenv("DIST_DIR")
    if dist_dir:
        return ["--dist-dir", dist_dir]
    else:
        return []


def _setup_kw(pkgdef):
    project_dir = os.path.dirname(pkgdef.guildfile.src)
    summary, help_desc = _pkg_description(pkgdef)
    project_name = pkgdef.name
    python_pkg_name = _python_pkg_name(pkgdef)
    packages, package_dir = _python_packages(pkgdef, python_pkg_name, project_dir)
    return dict(
        name=project_name,
        version=pkgdef.version,
        description=summary,
        long_description=help_desc,
        long_description_content_type="text/x-rst",
        url=pkgdef.url,
        author=pkgdef.author,
        author_email=pkgdef.author_email,
        license=pkgdef.license,
        keywords=_pkg_keywords(pkgdef),
        python_requires=pkgdef.python_requires,
        install_requires=_pkg_install_requires(pkgdef),
        packages=packages,
        package_dir=package_dir,
        namespace_packages=_namespace_packages(python_pkg_name),
        package_data={python_pkg_name: _package_data(pkgdef)},
        entry_points=_entry_points(pkgdef),
    )


def _pkg_description(pkgdef):
    """Returns a tuple of the package summary and long description.

    The summary is the first line of the package description
    field. Long description is generated using Guild's help generafor
    the package description (restructured text format).

    """
    pkg_desc_lines = pkgdef.description.split("\n")
    summary = pkg_desc_lines[0]
    help_desc = helplib.package_description(pkgdef.guildfile)
    return summary, help_desc


def _python_pkg_name(pkgdef):
    return pkgdef.name.replace("-", "_")


def _python_packages(pkgdef, base_pkg, project_dir):
    if pkgdef.packages is not None:
        return pkgdef.packages.keys(), pkgdef.packages
    return _default_python_packages(base_pkg, project_dir)


def _default_python_packages(base_pkg, project_dir):
    found_pkgs = setuptools.find_packages()
    if base_pkg in found_pkgs:
        _exit(
            "guild: package name '%s' in guild.yml conflicts with Python package '%s'\n"
            "Provide a unique package name in guild.yml and try again."
            % (base_pkg, base_pkg)
        )
    all_pkgs = [base_pkg] + _apply_base_pkg(base_pkg, found_pkgs)
    pkg_dirs = _all_pkg_dirs(project_dir, base_pkg, found_pkgs)
    return all_pkgs, pkg_dirs


def _apply_base_pkg(base_pkg, found_pkgs):
    return ["%s.%s" % (base_pkg, pkg) for pkg in found_pkgs]


def _all_pkg_dirs(project_dir, base_pkg, found_pkgs):
    pkg_dirs = {base_pkg: project_dir}
    pkg_dirs.update(
        {
            found_pkg: os.path.join(project_dir, found_pkg.replace(".", os.path.sep))
            for found_pkg in found_pkgs
        }
    )
    return pkg_dirs


def _namespace_packages(python_pkg_name):
    parts = python_pkg_name.rsplit(".", 1)
    if len(parts) == 1:
        return []
    else:
        return [parts[0]]


def _package_data(pkgdef):
    return _pkg_data_files(pkgdef) + _default_pkg_files()


def _pkg_data_files(pkgdef):
    matches = []
    for pattern in pkgdef.data_files:
        files = _match_data_files_pattern(pattern)
        if not files:
            log.warning("Nothing matched data file pattern '%s'", pattern)
        else:
            log.debug("files matching '%s': %s", pattern, files)
        matches.extend(files)
    return matches


def _match_data_files_pattern(pattern):
    if os.path.isdir(pattern):
        return _all_files_for_dir(pattern)
    else:
        return glob.glob(pattern)


def _all_files_for_dir(dir):
    return [os.path.join(dir, path) for path in file_util.find(dir, followlinks=True)]


def _default_pkg_files():
    return [
        guildfile.NAME,
        "LICENSE",
        "LICENSE.*",
        "README",
        "README.*",
    ]


def _entry_points(pkgdef):
    return {
        name: eps
        for name, eps in [
            ("guild.models", _model_entry_points(pkgdef)),
            ("guild.resources", _resource_entry_points(pkgdef)),
        ]
        if eps
    }


def _model_entry_points(pkgdef):
    models = sorted(pkgdef.guildfile.models.values(), key=lambda m: m.name)
    return [
        "%s = guild.model:PackageModel" % _model_entry_point_name(model)
        for model in models
    ]


def _model_entry_point_name(model):
    return model.name or "__anonymous__"


def _resource_entry_points(pkgdef):
    return _model_resource_entry_points(pkgdef)


def _model_resource_entry_points(pkgdef):
    return [
        (
            "%s:%s = guild.model:PackageModelResource"
            % (resdef.modeldef.name, resdef.name)
        )
        for resdef in _iter_guildfile_resdefs(pkgdef)
    ]


def _iter_guildfile_resdefs(pkgdef):
    for modeldef in pkgdef.guildfile.models.values():
        for resdef in modeldef.resources:
            yield resdef


def _pkg_keywords(pkgdef):
    tags = list(pkgdef.tags)
    if "gpkg" not in tags:
        tags.append("gpkg")
    return " ".join(tags)


def _pkg_install_requires(pkgdef):
    if pkgdef.requires is None:
        return _maybe_requirements_txt(pkgdef)
    elif not pkgdef.requires:
        return []
    else:
        return [
            _project_name(req) for req in pkgdef.requires if not _is_multi_arch_req(req)
        ]


def _maybe_requirements_txt(pkgdef):
    requirements_txt = os.path.join(pkgdef.guildfile.dir, "requirements.txt")
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


def _write_package_metadata(pkgdef, setup_kw):
    egg_info_dir = "%s.egg-info" % setup_kw["name"]
    util.ensure_dir(egg_info_dir)
    dest = os.path.join(egg_info_dir, "PACKAGE")
    with open(dest, "w") as f:
        yaml.dump(_pkg_metadata(pkgdef), f, default_flow_style=False, width=9999)


def _pkg_metadata(pkgdef):
    for item in pkgdef.guildfile.data:
        if "package" in item:
            return _coerce_pkg_data(item)
    return {}


def _coerce_pkg_data(data):
    return {attr: _coerce_pkg_attr(attr, val) for attr, val in data.items()}


def _coerce_pkg_attr(name, val):
    if name == "requires" and isinstance(val, six.string_types):
        return [val]
    return val


def _maybe_upload(dist):
    upload_repo = os.getenv("UPLOAD_REPO")
    if upload_repo:
        _upload(dist, upload_repo)


def _upload(dist, upload_repo):
    from twine.commands import upload

    _check_wheel_metadata_version(dist)
    args = _twine_upload_args(dist, upload_repo)
    try:
        upload.main(args)
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
            % (metadata_ver, ", ".join(map(repr, supported_vers)))
        )


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
    from twine import utils

    config = utils.get_config()
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
        log.exception("twine error")
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
