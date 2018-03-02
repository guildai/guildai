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

import logging
import os
import re
import sys

from pip.commands.download import DownloadCommand
from pip.commands.install import InstallCommand
from pip.commands.search import SearchCommand
from pip.commands.show import ShowCommand
from pip.commands.uninstall import UninstallCommand
from pip.download import _download_http_url
from pip.exceptions import HashMismatch as HashMismatch0
from pip.exceptions import InstallationError
from pip.exceptions import UninstallationError
from pip.index import Link
from pip.locations import running_under_virtualenv
from pip.utils import get_installed_distributions
from pip.utils.hashes import Hashes

from guild import namespace
from guild import util

log = logging.getLogger("guild")

class InstallError(Exception):
    pass

def install(reqs, index_urls=None, upgrade=False, pre_releases=False,
            no_cache=False, reinstall=False):
    _ensure_patch_pip_get_entry_points()
    cmd = InstallCommand()
    args = []
    if pre_releases:
        args.append("--pre")
    if not running_under_virtualenv():
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
    try:
        cmd.run(options, cmd_args)
    except InstallationError as e:
        raise InstallError(str(e))

def _ensure_patch_pip_get_entry_points():
    """Patch pip's get_entrypoints function.

    Older versions of pip use configparse to load the entrypoints file
    in a wheel, which imposes its own syntax requirements on entry
    point keys causing problems for our key naming conventions.

    We replace their `get_entrypoints` which is
    `_get_entrypoints_patch`, which is copied from their more recent
    source.
    """
    import pip.wheel
    if pip.wheel.get_entrypoints != _pip_get_entrypoints_patch:
        pip.wheel.get_entrypoints = _pip_get_entrypoints_patch

def _pip_get_entrypoints_patch(filename):
    """See `_ensure_pip_get_entrypoints_patch` for details."""
    from pip._vendor.six import StringIO
    from pip._vendor import pkg_resources

    if not os.path.exists(filename):
        return {}, {}

    # This is done because you can pass a string to entry_points wrappers which
    # means that they may or may not be valid INI files. The attempt here is to
    # strip leading and trailing whitespace in order to make them valid INI
    # files.
    with open(filename) as fp:
        data = StringIO()
        for line in fp:
            data.write(line.strip())
            data.write("\n")
        data.seek(0)

    # get the entry points and then the script names
    entry_points = pkg_resources.EntryPoint.parse_map(data)
    console = entry_points.get('console_scripts', {})
    gui = entry_points.get('gui_scripts', {})

    def _split_ep(s):
        """get the string representation of EntryPoint, remove space and split
        on '='"""
        return str(s).replace(" ", "").split("=")

    # convert the EntryPoint objects into strings with module:function
    console = dict(_split_ep(v) for v in console.values())
    gui = dict(_split_ep(v) for v in gui.values())
    return console, gui

def get_installed():
    user_only = not running_under_virtualenv()
    return get_installed_distributions(
        local_only=False,
        user_only=user_only)

def search(terms):
    _ensure_search_logger()
    cmd = SearchCommand()
    args = terms
    options, query = cmd.parse_args(args)
    return cmd.search(query, options)

class QuietLogger(logging.Logger):

    def __init__(self, parent):
        super(QuietLogger, self).__init__(parent.name)
        self.parent = parent
        self.level = logging.WARNING

def _ensure_search_logger():
    from pip._vendor.requests.packages.urllib3 import connectionpool
    if not isinstance(connectionpool.log, QuietLogger):
        connectionpool.log = QuietLogger(connectionpool.log)

def uninstall(reqs, dont_prompt=False):
    cmd = UninstallCommand()
    for req in reqs:
        _uninstall(req, cmd, dont_prompt)

def _uninstall(req, cmd, dont_prompt):
    args = [req]
    if dont_prompt:
        args.append("--yes")
    options, cmd_args = cmd.parse_args(args)
    try:
        cmd.run(options, cmd_args)
    except UninstallationError as e:
        if "not installed" not in str(e):
            raise
        log.warning("%s is not installed, skipping", req)

class HashMismatch(Exception):

    def __init__(self, url, expected, actual):
        super(HashMismatch, self).__init__()
        self.path = url
        self.expected = expected
        self.actual = actual

def download_url(url, download_dir, sha256=None):
    cmd = DownloadCommand()
    # We disable cache control for downloads for two reasons: First,
    # we're already caching our downloads as resources, so an
    # additional level of caching, even if efficiently managed, is
    # probably not worth the cost. Second, the cachecontrol module
    # used with pip's download facility is unusable with large files
    # as it loads files into memory:
    #
    # https://github.com/ionrock/cachecontrol/issues/145
    #
    options, _ = cmd.parse_args(["--no-cache-dir"])
    link = Link(url)
    session = cmd._build_session(options)
    hashes = Hashes({"sha256": [sha256]}) if sha256 else None
    download_path = _check_download_dir(link, download_dir, hashes)
    if not download_path:
        try:
            download_raw, _ = _download_http_url(
                Link(url),
                session,
                download_dir,
                hashes)
        except HashMismatch0 as e:
            expected = e.allowed["sha256"][0]
            actual = e.gots["sha256"].hexdigest()
            raise HashMismatch(url, expected, actual)
        else:
            download_path = _ensure_expected_download_path(download_raw, link)
    if hashes:
        _cache_hashes(hashes, download_path)
    return download_path

def _check_download_dir(link, download_dir, hashes):
    # Mirrors pip.download._check_download_dir but uses sha cache.
    download_path = os.path.join(download_dir, link.filename)
    if not os.path.exists(download_path):
        return None
    log.info("Using cached file %s", download_path)
    if not hashes:
        return download_path
    cached_sha = util.try_cached_sha(download_path)
    if cached_sha and cached_sha == _allowed_sha(hashes):
        return download_path
    try:
        hashes.check_against_path(download_path)
    except HashMismatch0:
        log.warning(
            "Cached file %s has bad hash - re-downloading",
            download_path
        )
        os.unlink(download_path)
        return None
    else:
        return download_path

def _allowed_sha(hashes):
    allowed = hashes._allowed
    assert list(allowed.keys()) == ["sha256"], allowed
    sha256_hashes = allowed["sha256"]
    assert len(sha256_hashes) == 1, allowed
    return sha256_hashes[0]

def _cache_hashes(hashes, download_path):
    util.write_cached_sha(_allowed_sha(hashes), download_path)

def _ensure_expected_download_path(downloaded, link):
    expected = os.path.join(os.path.dirname(downloaded), link.filename)
    if downloaded != expected:
        os.rename(downloaded, expected)
    return expected

def print_package_info(pkg, verbose=False, show_files=False):
    _ensure_print_package_logger()
    cmd = ShowCommand()
    args = []
    if verbose:
        args.append("--verbose")
    if show_files:
        args.append("--files")
    args.append(pkg)
    return cmd.run(*cmd.parse_args(args))

class PrintPackageLogger(object):

    def info(self, msg, args=None):
        args = args or []
        out = self._normalize_attr_case(msg % args)
        out = self._apply_namespace(out)
        sys.stdout.write(out)
        sys.stdout.write("\n")

    @staticmethod
    def _normalize_attr_case(s):
        m = re.match("([^:]+:)(.*)", s)
        if m:
            return m.group(1).lower() + m.group(2)
        return s

    @staticmethod
    def _apply_namespace(s):
        if s[:6] == "name: ":
            project_name = s[6:]
            package_name = namespace.apply_namespace(project_name)
            return "name: %s" % package_name
        return s

def _ensure_print_package_logger():
    from pip.commands import show
    if not isinstance(show.logger, PrintPackageLogger):
        show.logger = PrintPackageLogger()
