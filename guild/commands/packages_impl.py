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

import logging
import os
import re

import six

from guild import cli
from guild import namespace
from guild import pip_util
from guild import util

log = logging.getLogger("guild")

def list_packages(args):
    installed = pip_util.get_installed()
    packages = [pkg for pkg in installed if args.all or _is_gpkg(pkg)]
    formatted = [_format_pkg(pkg) for pkg in packages]
    filtered = [pkg for pkg in formatted if _filter_model(pkg, args)]
    cli.table(filtered, cols=["name", "version", "summary"], sort=["name"])

def _is_gpkg(pkg):
    keywords = _pkg_metadata(pkg, "Keywords") or ""
    return "gpkg" in keywords.split(" ")

def _pkg_metadata(pkg, name):
    try:
        metadata_lines = pkg.get_metadata_lines("METADATA")
    except IOError:
        # no METADATA
        metadata_lines = []
    line_prefix = "{}: ".format(name)
    len_line_prefix = len(line_prefix)
    for line in metadata_lines:
        if line[:len_line_prefix] == line_prefix:
            return line[len_line_prefix:]
    return None

def _format_pkg(pkg):
    return {
        "name": pkg.project_name,
        "summary": _strip_guildai_suffix(_pkg_metadata(pkg, "Summary") or ""),
        "version": pkg.version,
    }

def _strip_guildai_suffix(summary):
    return re.sub(r" \(Guild AI\)$", "", summary)

def _filter_model(pkg, args):
    to_search = [
        six.u(pkg["name"]),
        six.u(pkg["summary"])
    ]
    return util.match_filters(args.terms, to_search)

def install_packages(args):
    for reqs, index_urls in _installs(args.packages):
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
    pip_util.uninstall(args.packages, dont_prompt=args.yes)

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
