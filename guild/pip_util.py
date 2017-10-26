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

import re

from pip.exceptions import UninstallationError
from pip.commands.install import InstallCommand
from pip.commands.search import SearchCommand
from pip.commands.uninstall import UninstallCommand
from pip.locations import virtualenv_no_global
from pip.utils import get_installed_distributions

class NotInstalledError(Exception):

    def __init__(self, req):
        super(NotInstalledError, self).__init__(
            "%s is not installed" % req)
        self.req = req

def install(reqs, index_urls=None, upgrade=False, pre_releases=False,
            no_cache=False, reinstall=False):
    cmd = InstallCommand()
    args = []
    if pre_releases:
        args.append("--pre")
    if not virtualenv_no_global():
        args.append("--user")
    if upgrade:
        args.append("--upgrade")
    if no_cache:
        args.append("--no-cache-dir")
    if reinstall:
        args.append("--force-reinstall")
    if index_urls:
        args.extend(["--index-url", index_urls[0]])
        for url in index_urls[1:]:
            args.extend(["--extra-index-url", url])
    args.extend(reqs)
    options, cmd_args = cmd.parse_args(args)
    cmd.run(options, cmd_args)

def get_installed():
    user_only = not virtualenv_no_global()
    return get_installed_distributions(
        local_only=False,
        user_only=user_only)

def search(terms):
    cmd = SearchCommand()
    args = terms
    options, query = cmd.parse_args(args)
    return cmd.search(query, options)

def uninstall(reqs, dont_prompt=False):
    cmd = UninstallCommand()
    args = []
    if dont_prompt:
        args.append("--yes")
    args.extend(reqs)
    options, cmd_args = cmd.parse_args(args)
    try:
        cmd.run(options, cmd_args)
    except UninstallationError as e:
        m = re.match(
            "Cannot uninstall requirement (.+?), not installed",
            e.message)
        if m:
            raise NotInstalledError(m.group(1))
        raise
