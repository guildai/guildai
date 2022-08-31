# Copyright 2017-2022 RStudio, PBC
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

import logging
import os
import re
import subprocess
import sys

from guild import util

log = logging.getLogger("guild")


class InstallError(Exception):
    pass


def install(
    reqs,
    index_urls=None,
    upgrade=False,
    pre_releases=False,
    no_cache=False,
    no_deps=False,
    reinstall=False,
    target=None,
):

    _reset_env_for_install()
    args = [sys.executable, "-m", "pip", "install"]
    if pre_releases:
        args.append("--pre")
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

    for req in reqs:
        if req.endswith("requirements.txt"):
            args.append("--requirement")
        args.append(req)

    try:
        return subprocess.check_call(args)
    except subprocess.CalledProcessError as e:
        raise InstallError(str(e)) from e


def _reset_env_for_install():
    util.del_env(["PIP_REQ_TRACKER"])


def running_under_virtualenv():
    return "VIRTUAL_ENV" in os.environ or "CONDA_PREFIX" in os.environ


def get_installed():
    if sys.version_info >= (3, 8):
        from importlib import metadata as importlib_metadata
    else:
        import importlib_metadata
    return importlib_metadata.distributions()


class QuietLogger(logging.Logger):
    def __init__(self, parent):
        super().__init__(parent.name)
        self.parent = parent
        self.level = logging.WARNING


def uninstall(reqs, dont_prompt=False):
    for req in reqs:
        _uninstall(req, dont_prompt)


def _uninstall(req, dont_prompt):
    args = [sys.executable, "-m", "pip", "uninstall"]
    if dont_prompt:
        args.append("--yes")
    args.append(req)
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError as e:
        if "not installed" in str(e):
            log.warning("%s is not installed, skipping", req)
        else:
            raise


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

    from urllib.parse import urlparse, unquote
    import urllib.request

    filename = unquote(urlparse(url).path.split("/")[-1])

    downloaded_path = _check_download_path(filename, download_dir, sha256)
    if not downloaded_path:
        orig_path = os.path.join(download_dir, filename)
        urllib.request.urlretrieve(url, orig_path)
        downloaded_path = _ensure_expected_download_path(orig_path, filename)
        if sha256:
            _verify_and_cache_hash(downloaded_path, sha256)
    return downloaded_path


def _check_download_path(filename, download_dir, expected_hash):
    download_path = os.path.join(download_dir, filename)
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
        super().__init__(path, expected, actual)
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


def _ensure_expected_download_path(downloaded, filename):
    expected = os.path.join(os.path.dirname(downloaded), filename)
    if downloaded != expected:
        os.rename(downloaded, expected)
    return expected


def _normalize_attr_case(s):
    m = re.match("([^:]+:)(.*)", s)
    if m:
        return m.group(1).lower() + m.group(2)
    return s


def print_package_info(pkg, verbose=False, show_files=False):
    args = [sys.executable, "-m", "pip", "show"]
    if verbose:
        args.append("--verbose")
    if show_files:
        args.append("--files")
    args.append(pkg)
    try:
        lines = subprocess.check_output(args).splitlines()
        for line in lines:
            print(
                _normalize_attr_case(
                    line.decode('utf-8') if hasattr(line, 'decode') else line
                ).rstrip()
            )
        return 0
    except:
        return f"Failed to get package info for {pkg}"


def is_requirements(path):
    from pkg_resources import parse_requirements

    if not util.is_text_file(path):
        return False
    try:
        with open(path) as f:
            list(parse_requirements(f.readlines()))
    except Exception:
        return False
    else:
        return True


def _distutils_scheme(
    dist_name, user=False, home=None, root=None, isolated=False, prefix=None
):
    """
    Return a distutils install scheme

    This function is vendored from pip.
    """
    from setuptools.dist import Distribution

    def running_under_virtualenv():
        """Return True if we're running inside a virtualenv, False otherwise."""
        if hasattr(sys, 'real_prefix'):
            return True
        if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
            return True
        return False

    scheme = {}

    if isolated:
        extra_dist_args = {"script_args": ["--no-user-cfg"]}
    else:
        extra_dist_args = {}
    dist_args = {'name': dist_name}
    dist_args.update(extra_dist_args)

    d = Distribution(dist_args)
    d.parse_config_files()
    i = d.get_command_obj('install', create=True)
    # NOTE: setting user or home has the side-effect of creating the home dir
    # or user base for installations during finalize_options()
    # ideally, we'd prefer a scheme class that has no side-effects.
    assert not (user and prefix), f"user={user} prefix={prefix}"
    i.user = user or i.user
    if user:
        i.prefix = ""
    i.prefix = prefix or i.prefix
    i.home = home or i.home
    i.root = root or i.root
    i.finalize_options()
    for key in ('purelib', 'platlib', 'headers', 'scripts', 'data'):
        scheme[key] = getattr(i, 'install_' + key)

    # install_lib specified in setup.cfg should install *everything*
    # into there (i.e. it takes precedence over both purelib and
    # platlib).  Note, i.install_lib is *always* set after
    # finalize_options(); we only want to override here if the user
    # has explicitly requested it hence going back to the config
    if 'install_lib' in d.get_option_dict('install'):
        scheme.update(dict(purelib=i.install_lib, platlib=i.install_lib))

    if running_under_virtualenv():
        scheme['headers'] = os.path.join(
            sys.prefix,
            'include',
            'site',
            'python' + sys.version[:3],
            dist_name,
        )

        if root is not None:
            path_no_drive = os.path.splitdrive(os.path.abspath(scheme["headers"]))[1]
            scheme["headers"] = os.path.join(
                root,
                path_no_drive[1:],
            )

    return scheme


dist_info_re = re.compile(
    r"""^(?P<namever>(?P<name>.+?)(-(?P<ver>\d.+?))?)
                                \.dist-info$""",
    re.VERBOSE,
)


def root_is_purelib(name, wheeldir):
    """
    Return True if the extracted wheel in wheeldir should go into purelib.
    """
    name_folded = name.replace("-", "_")
    for item in os.listdir(wheeldir):
        match = dist_info_re.match(item)
        if match and match.group('name') == name_folded:
            with open(os.path.join(wheeldir, item, 'WHEEL')) as wheel:
                for line in wheel:
                    line = line.lower().rstrip()
                    if line == "root-is-purelib: true":
                        return True
    return False


def lib_dir(
    name,
    wheeldir,
    user=False,
    home=None,
    root=None,
    isolated=False,
    prefix=None,
):
    scheme = _distutils_scheme(
        "", user=user, home=home, root=root, isolated=isolated, prefix=prefix
    )
    if root_is_purelib(name, wheeldir):
        return scheme['purelib']
    return scheme['platlib']


def freeze():
    try:
        return subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"], stdin=subprocess.DEVNULL
        ).splitlines()
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("reading pip freeze")
        else:
            log.warning("error reading pip freeze: %s", e)
        return None
