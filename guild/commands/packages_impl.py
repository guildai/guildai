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

import guild.cli
import guild.cmd_support
import guild.package
import guild.pip_util

def list_packages(_args):
    pkgs = [_format_pkg(pkg) for pkg in guild.pip_util.get_installed()]
    guild.cli.table(pkgs, cols=["name", "version"], sort=["name"])

def _format_pkg(pkg):
    return {
        "name": guild.package.apply_namespace(pkg.name),
        "version": pkg.version,
    }

def install_packages(args):
    for reqs, index_urls in _installs(args):
        print(
            "TODO: install %s (index=%s, upgrade=%s)"
            % (reqs, index_urls, args.upgrade))
        #guild.pip_util.install(reqs, index_urls, args.upgrade)

def _installs(args):
    index_urls = {}
    for pkg in args.packages:
        ns, req_in = guild.cmd_support.split_pkg(pkg)
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
