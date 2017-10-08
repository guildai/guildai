import logging
import os

from pip._internal.commands.download import DownloadCommand
from pip._internal.commands.install import InstallCommand
from pip._internal.wheel import Wheel

import guild.var

def install_package(name, force=False):
    reqs = _download(name)
    for req_name, req in reqs.requirements.items():
        _ensure_installed(req, force)

def _download(name):
    cmd = DownloadCommand()
    args = [
        name,
        "-d", guild.var.cache_dir("pkgsrc"),
        "--no-cache-dir"
    ]
    return cmd.run(*cmd.parse_args(args))

def _ensure_installed(req, force):
    pkg_dest, pkg_info = _req_pkg_dest(req)
    if force or not os.path.exists(pkg_dest):
        archive_src = _req_archive_src(req)
        _install(archive_src, pkg_dest)
    else:
        name, version = pkg_info
        logging.info("Skipped %s-%s (already installed)", name, version)

def _req_pkg_dest(req):
    name = req.name
    version = _req_pkg_version(req)
    dest = guild.var.pkg_dir(name, version)
    return dest, (name, version)

def _req_pkg_version(req):
    link = req.link
    if link.is_wheel:
        return Wheel(link.filename).version
    elif link.filename.endswith(".tar.gz"):
        return Wheel(_wheel_name_from_tar_gz(link.filename)).version
    else:
        raise AssertionError(link.filename)

def _wheel_name_from_tar_gz(filename):
    return "%s-py-none-any.whl" % filename[:-7]

def _req_archive_src(req):
    return os.path.join(guild.var.cache_dir("pkgsrc"), req.link.filename)

def _install(archive_src, dest_dir):
    cmd = InstallCommand()
    args = [
        "--no-deps",
        "--upgrade",
        "-t", dest_dir,
        archive_src
    ]
    return cmd.run(*cmd.parse_args(args))
