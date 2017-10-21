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

from guild import cli
from guild import cmd_impl_support
from guild import pip_util
from guild import package

def list_packages(args):
    installed = pip_util.get_installed()
    filtered = _filter_packages(installed, args)
    pkgs = [_format_pkg(pkg) for pkg in filtered]
    cli.table(pkgs, cols=["name", "version"], sort=["name"])

def _filter_packages(pkgs, args):
    if args.all:
        return pkgs
    return [pkg for pkg in pkgs if package.is_gpkg(pkg.project_name)]

def _format_pkg(pkg):
    return {
        "name": package.apply_namespace(pkg.project_name),
        "version": pkg.version,
    }

def install_packages(args):
    for reqs, index_urls in _installs(args):
        print(
            "TODO: install %s (index=%s, upgrade=%s)"
            % (reqs, index_urls, args.upgrade))
        #pip_util.install(reqs, index_urls, args.upgrade)

def _installs(args):
    index_urls = {}
    for pkg in args.packages:
        # TODO: fix
        ns, req_in = cmd_impl_support.split_pkg(pkg)
        req, urls = ns.pip_install_info(req_in)
        urls_key = "\n".join(urls)
        index_urls.setdefault(urls_key, []).append(req)
    return [
        (reqs, urls_key.split("\n"))
        for urls_key, reqs in index_urls.items()
    ]

def delete_packages(args):
    print("TODO: delete %s" % args.packages)

def uninstall_packages(args):
    print("TODO: uninstall %s" % (args.packages,))

def package_info(args):
    print("TODO: show info for %s" % args.package)
