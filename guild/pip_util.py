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
import sys

from six.moves import xmlrpc_client

from pip._internal.commands.download import DownloadCommand
from pip._internal.commands.install import InstallCommand
from pip._internal.commands.search import SearchCommand as SearchCommandBase
from pip._internal.commands.show import ShowCommand
from pip._internal.commands.uninstall import UninstallCommand
from pip._internal.download import _download_http_url
from pip._internal.download import PipXmlrpcTransport
from pip._internal.exceptions import InstallationError
from pip._internal.exceptions import UninstallationError
from pip._internal.index import Link
from pip._internal.locations import distutils_scheme
from pip._internal.req import req_file
from pip._internal.utils.misc import get_installed_distributions
from pip._internal.wheel import root_is_purelib

from guild import util

log = logging.getLogger("guild")

class InstallError(Exception):
    pass

class SearchCommand(SearchCommandBase):
    """Guild specific pip search implementation.

    This exposes the search fields and operator, which were are hard
    coded in the pip implementation.
    """

    def __init__(self, spec, operator, *args, **kw):
        super(SearchCommand, self).__init__(*args, **kw)
        self._spec = spec
        self._operator = operator

    def search(self, _query, options):
        index_url = options.index
        with self._build_session(options) as session:
            transport = PipXmlrpcTransport(index_url, session)
            pypi = xmlrpc_client.ServerProxy(index_url, transport)
            return pypi.search(self._spec, self._operator)

def install(reqs, index_urls=None, upgrade=False, pre_releases=False,
            no_cache=False, no_deps=False, reinstall=False, target=None):
    _reset_env_for_install()
    _ensure_patch_pip_get_entry_points()
    cmd = _pip_cmd(InstallCommand)
    args = []
    if pre_releases:
        args.append("--pre")
    if not running_under_virtualenv() and not target:
        args.append("--user")
    if upgrade:
        args.append("--upgrade")
    if no_cache:
        args.append("--no-cache-dir")
    if no_deps:
        args.append("--no-deps")
    if reinstall:
        args.append("--force-reinstall")
    if index_urls:
        args.extend(["--index-url", index_urls[0]])
        for url in index_urls[1:]:
            args.extend(["--extra-index-url", url])
    if target:
        args.extend(["--target", target])
    args.extend(reqs)
    options, cmd_args = cmd.parse_args(args)
    try:
        return cmd.run(options, cmd_args)
    except InstallationError as e:
        raise InstallError(str(e))

def _reset_env_for_install():
    util.del_env(["PIP_REQ_TRACKER"])

def _pip_cmd(cls, *args, **kw):
    cmd = cls(*args, **kw)
    cmd.verbosity = False
    return cmd

def running_under_virtualenv():
    return "VIRTUAL_ENV" in os.environ or "CONDA_PREFIX" in os.environ

def _ensure_patch_pip_get_entry_points():
    """Patch pip's get_entrypoints function.

    Older versions of pip use configparse to load the entrypoints file
    in a wheel, which imposes its own syntax requirements on entry
    point keys causing problems for our key naming conventions.

    We replace their `get_entrypoints` which is
    `_get_entrypoints_patch`, which is copied from their more recent
    source.
    """
    from pip._internal import wheel
    if wheel.get_entrypoints != _pip_get_entrypoints_patch:
        wheel.get_entrypoints = _pip_get_entrypoints_patch

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

def search(spec, operator):
    _ensure_search_logger()
    cmd = _pip_cmd(SearchCommand, spec, operator)
    options, unused_parsed_query = cmd.parse_args([])
    return cmd.search(unused_parsed_query, options)

class QuietLogger(logging.Logger):

    def __init__(self, parent):
        super(QuietLogger, self).__init__(parent.name)
        self.parent = parent
        self.level = logging.WARNING

def _ensure_search_logger():
    try:
        from pip._vendor.requests.packages.urllib3 import connectionpool
    except ImportError:
        pass
    else:
        if not isinstance(connectionpool.log, QuietLogger):
            connectionpool.log = QuietLogger(connectionpool.log)

def uninstall(reqs, dont_prompt=False):
    cmd = _pip_cmd(UninstallCommand)
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

def download_url(url, download_dir, sha256=None):
    """Download and optionally verify a file.

    Returns the downloaded file path.

    If sha256 is not specified (default), the file is not verified.

    Raises HashMismatch if the file hash does not match the specified
    sha256 hash.

    If the file was already downloaded, returns its path after
    verifying it. If the file cannot be verified, raises HashMismatch
    without attempting download again. If the hash is valid but the
    download is not, the download must be deleted before trying
    again. This behavior is designed to preserve downloads at the cost
    of requiring that invalid files be explicitly deleted.

    """
    link = Link(url)
    downloaded_path = _check_download_path(link, download_dir, sha256)
    if not downloaded_path:
        orig_path = _pip_download(link, download_dir)
        downloaded_path = _ensure_expected_download_path(orig_path, link)
        if sha256:
            _verify_and_cache_hash(downloaded_path, sha256)
    return downloaded_path

def _check_download_path(link, download_dir, expected_hash):
    download_path = os.path.join(download_dir, link.filename)
    if not os.path.exists(download_path):
        return None
    log.info("Using cached file %s", download_path)
    if not expected_hash:
        return download_path
    cached_hash = util.try_cached_sha(download_path)
    if cached_hash and cached_hash == expected_hash:
        return download_path
    _verify_and_cache_hash(download_path, expected_hash)
    return download_path

class HashMismatch(Exception):

    def __init__(self, path, expected, actual):
        super(HashMismatch, self).__init__(path, expected, actual)
        self.path = path
        self.expected = expected
        self.actual = actual

def _verify_and_cache_hash(path, expected_hash):
    calculated_hash = util.file_sha256(path)
    if calculated_hash != expected_hash:
        raise HashMismatch(path, expected_hash, calculated_hash)
    _cache_sha256(calculated_hash, path)

def _cache_sha256(sha256, download_path):
    util.write_cached_sha(sha256, download_path)

def _pip_download(link, download_dir):
    # We disable cache control for downloads for two reasons: First,
    # we're already caching our downloads as resources, so an
    # additional level of caching, even if efficiently managed, is
    # probably not worth the cost. Second, the cachecontrol module
    # used with pip's download facility is unusable with large files
    # as it reads files into memory:
    #
    # https://github.com/ionrock/cachecontrol/issues/145
    #
    cmd = _pip_cmd(DownloadCommand)
    options, _ = cmd.parse_args(["--no-cache-dir"])
    session = cmd._build_session(options)
    orig_path, _ = _download_http_url(link, session, download_dir,
                                      hashes=None, progress_bar="on")
    return orig_path

def _ensure_expected_download_path(downloaded, link):
    expected = os.path.join(os.path.dirname(downloaded), link.filename)
    if downloaded != expected:
        os.rename(downloaded, expected)
    return expected

def print_package_info(pkg, verbose=False, show_files=False):
    _ensure_print_package_logger()
    cmd = _pip_cmd(ShowCommand)
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
        sys.stdout.write(out)
        sys.stdout.write("\n")

    @staticmethod
    def _normalize_attr_case(s):
        m = re.match("([^:]+:)(.*)", s)
        if m:
            return m.group(1).lower() + m.group(2)
        return s

def _ensure_print_package_logger():
    from pip._internal.commands import show
    if not isinstance(show.logger, PrintPackageLogger):
        show.logger = PrintPackageLogger()

def parse_requirements(path):
    return req_file.parse_requirements(path, session="unused")

def is_requirements(path):
    if not util.is_text_file(path):
        return False
    try:
        list(parse_requirements(path))
    except Exception:
        return False
    else:
        return True

def lib_dir(name, wheeldir, user=False, home=None, root=None,
            isolated=False, prefix=None):
    scheme = distutils_scheme(
        "", user=user, home=home, root=root,
        isolated=isolated, prefix=prefix)
    if root_is_purelib(name, wheeldir):
        return scheme['purelib']
    else:
        return scheme['platlib']
