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

import glob
import logging
import os

from guild import cli
from guild import guildfile
from guild import namespace
from guild import package
from guild import pip_util
from guild import util

log = logging.getLogger("guild")

INTERNAL_PACKAGES = ["guildai"]

def list_packages(args):
    installed = pip_util.get_installed()
    scope_filtered = [pkg for pkg in installed if _filter_scope(pkg, args)]
    formatted = [_format_pkg(pkg) for pkg in scope_filtered]
    filtered = [pkg for pkg in formatted if _filter_model(pkg, args)]
    cli.table(filtered, cols=["name", "version", "summary"], sort=["name"])

def _filter_scope(pkg, args):
    return (
        pkg.project_name not in INTERNAL_PACKAGES
        and (args.all or package.is_gpkg(pkg.project_name))
    )

def _format_pkg(pkg):
    return {
        "name": namespace.apply_namespace(pkg.project_name),
        "summary": _pkg_summary(pkg),
        "version": pkg.version,
    }

def _pkg_summary(pkg):
    try:
        metadata_lines = pkg.get_metadata_lines("METADATA")
    except IOError:
        # no METADATA
        metadata_lines = []
    # For efficiency, just look at the first few lines for Summary
    for i, line in enumerate(metadata_lines):
        if line[:9] == "Summary: ":
            return line[9:]
        if i == 5:
            break
    return ""

def _filter_model(pkg, args):
    return util.match_filters(args.terms, [pkg["name"], pkg["summary"]])

def install_packages(args):
    pip_pkgs, source_paths = _split_install_packages(args.packages)
    _install_guild_source_packages(source_paths, args)
    _install_pip_packages(pip_pkgs, args)

def _split_install_packages(pkgs):
    pip_pkgs = []
    source_paths = []
    for pkg in pkgs:
        if os.path.isdir(pkg):
            setup_path = os.path.join(pkg, "setup.py")
            if os.path.exists(setup_path):
                pip_paths.append(pkg)
            else:
                guildfile_path = os.path.join(pkg, "guild.yml")
                if os.path.exists(guildfile_path):
                    source_paths.append(guildfile_path)
                else:
                    cli.error(
                        "cannot install source directory %s: it "
                        "does not contain setup.py or guild.yml"
                        % pkg)
        else:
            pip_pkgs.append(pkg)
    return pip_pkgs, source_paths

def _install_guild_source_packages(source_paths, args):
    for guildfile_path in source_paths:
        project_path = os.path.dirname(guildfile_path)
        pkg_name = _guild_source_package_name(guildfile_path)
        dist_dir = util.mktempdir("guild-install-source-dist-")
        log.info("Building package %s from %s", pkg_name, project_path)
        package.create_package(guildfile_path, dist_dir)
        dist_wheel = _dist_wheel(dist_dir)
        log.info("Installing %s", pkg_name)
        installed = pip_util.install(
            [dist_wheel],
            upgrade=args.upgrade or args.reinstall,
            pre_releases=args.pre,
            no_cache=args.no_cache,
            no_deps=args.no_deps,
            reinstall=args.reinstall,
            target=args.target)
        log.info("Linking %s to source %s", pkg_name, project_path)
        _replace_installed_with_source_link(pkg_name, project_path, installed)
        util.rmtempdir(dist_dir)

def _guild_source_package_name(guildfile_path):
    try:
        gf = guildfile.from_file(guildfile_path)
    except guildfile.GuildfileError as e:
        cli.error(
            "error reading package name from %s: %s"
            % (guildfile_path, e))
    else:
        if not gf.package:
            project_path = os.path.dirname(guildfile_path)
            cli.error(
                "Guild package in %s does define a package"
                % project_path)
    return gf.package.name

def _dist_wheel(path):
    matches = glob.glob(os.path.join(path, "*.whl"))
    if not matches:
        cli.error(
            "error building Guild source in %s: wheel was not "
            "created in %s" % dist_dir)
    if len(matches) > 1:
        cli.error(
            "error building Guild source in %s: more than one wheel "
            "created in %s" % dist_dir)
    return matches[0]

def _replace_installed_with_source_link(pkg_name, project_path, installed):
    pip_project_name = namespace.pip_info(pkg_name).project_name
    assert pip_project_name in installed.requirements, installed
    installed_req = installed.requirements[pip_project_name]
    install_root = _req_install_root(installed_req)
    installed_pkg_path = os.path.join(
        install_root,
        pip_project_name.replace(".", os.path.sep))
    import pdb;pdb.set_trace()
    if os.path.islink(installed_pkg_path):
        os.remove(installed_pkg_path)
    else:
        util.safe_rmtree(installed_pkg_path)
    os.symlink(project_path, installed_pkg_path)

def _req_install_root(req):
    assert req.satisfied_by, req
    return req.satisfied_by.location

def _install_pip_packages(pip_pkgs, args):
    for reqs, index_urls in _installs(pip_pkgs):
        try:
            pip_util.install(
                reqs,
                index_urls=index_urls,
                upgrade=args.upgrade or args.reinstall,
                pre_releases=args.pre,
                no_cache=args.no_cache,
                no_deps=args.no_deps,
                reinstall=args.reinstall,
                target=args.target)
        except pip_util.InstallError as e:
            cli.error(str(e))

def _installs(pkgs):
    index_urls = {}
    for pkg in pkgs:
        if os.path.exists(pkg):
            index_urls.setdefault(None, []).append(pkg)
        else:
            info = _pip_info(pkg)
            urls_key = "\n".join(info.install_urls)
            index_urls.setdefault(urls_key, []).append(info.project_name)
    return [
        (reqs, urls_key.split("\n") if urls_key else [])
        for urls_key, reqs in index_urls.items()
    ]

def _pip_info(pkg):
    try:
        return namespace.pip_info(pkg)
    except namespace.NamespaceError as e:
        terms = " ".join(pkg.split("/")[1:])
        cli.error(
            "unsupported namespace %s in '%s'\n"
            "Try 'guild search %s -a' to find matching packages."
            % (e.value, pkg, terms))

def uninstall_packages(args):
    for reqs, _ in _installs(args.packages):
        pip_util.uninstall(reqs, dont_prompt=args.yes)

def package_info(args):
    for i, (project, pkg) in enumerate(_iter_project_names(args.packages)):
        if i > 0:
            cli.out("---")
        exit_status = pip_util.print_package_info(
            project,
            verbose=args.verbose,
            show_files=args.files)
        if exit_status != 0:
            log.warning("unknown package %s", pkg)

def _iter_project_names(pkgs):
    for pkg in pkgs:
        try:
            ns, name = namespace.split_name(pkg)
        except namespace.NamespaceError:
            log.warning("unknown namespace in '%s', ignoring", pkg)
        else:
            yield ns.pip_info(name).project_name, pkg
