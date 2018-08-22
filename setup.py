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

import glob
import os
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, "./guild/external")

from pip._internal.vcs.git import Git
from pkg_resources import Distribution as PkgDist
from pkg_resources import PathMetadata
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
from setuptools.dist import Distribution

import guild

from guild import util
from guild import log
from guild import pip_util

log.init_logging()

guild_dist_basename = "guildai.dist-info"

def guild_dist_info():
    metadata = PathMetadata(".", guild_dist_basename)
    dist = PkgDist.from_filename(guild_dist_basename, metadata)
    assert dist.project_name == "guildai", dist
    entry_points = {
        group: [str(ep) for ep in eps.values()]
        for group, eps in dist.get_entry_map().items()
    }
    return dist._parsed_pkg_info, entry_points

def guild_packages():
    return find_packages(exclude=["guild.tests", "guild.tests.*"])

PKG_INFO, ENTRY_POINTS = guild_dist_info()

EXTERNAL = {
    "click": ("guildai/click", "bde8dd59c66f0a0a0954ce8bb0105fc490a4f52d"),
    "psutil": ("giampaolo/psutil", "release-5.4.2"),
}

class BinaryDistribution(Distribution):

    @staticmethod
    def has_ext_modules():
        return True

class Build(build_py):
    """Extension of default build with additional pre-processing.

    In preparation for setuptool's default build, we perform these
    additional pre-processing steps:

    - Ensure external dependencies
    - Build view distribution
    - Build serve distribution

    See MANIFEST.in for a complete list of data files includes in the
    Guild distribution.
    """

    def run(self):
        _validate_env()
        _ensure_external()
        _build_view_dist()
        _build_serve_dist()
        build_py.run(self)

def _validate_env():
    try:
        subprocess.check_output(["npm", "--version"])
    except OSError as e:
        _exit("npm is not installed: %s", e)

def _exit(msg, *args):
    sys.stderr.write(msg % args)
    sys.stderr.write("\n")
    sys.exit(1)

def _ensure_external():
    """Ensure EXTERNAL deps are available."""

    for name in EXTERNAL:
        if os.path.exists(_external_marker(name)):
            continue
        _install_external(name, EXTERNAL[name])

def _external_marker(name):
    return os.path.join(
        "./guild/external",
        ".{}-py{}".format(name, sys.version_info[0]))

def _install_external(name, dist_spec):
    with util.TempDir(prefix="pip-", suffix="-download") as tmp:
        wheel_path = _pip_wheel(name, dist_spec, tmp)
        _install_external_wheel(wheel_path)
        util.touch(_external_marker(name))

def _pip_wheel(name, dist_spec, root):
    path, tag = dist_spec
    url = "git+https://github.com/{}@{}#egg={}".format(path, tag, name)
    src_dir = os.path.join(root, "src")
    build_dir = os.path.join(root, "src")
    wheel_dir = os.path.join(root, "wheel")
    assert not os.path.exists(wheel_dir), wheel_dir
    args = [
        "--editable", url,
        "--src", src_dir,
        "--build", build_dir,
        "--wheel-dir", wheel_dir,
    ]
    from pip._internal.commands.wheel import WheelCommand
    cmd = WheelCommand()
    options, cmd_args = cmd.parse_args(args)
    cmd.run(options, cmd_args)
    wheels = glob.glob(os.path.join(wheel_dir, "*.whl"))
    assert len(wheels) == 1, wheels
    return wheels[0]

def _install_external_wheel(wheel_path):
    zf = zipfile.ZipFile(wheel_path)
    util.ensure_dir("./guild/external")
    zf.extractall("./guild/external")

def _build_view_dist():
    """Build view distribution."""
    subprocess.check_call(["npm", "install"], cwd="./guild/view")
    subprocess.check_call(["npm", "run", "build"], cwd="./guild/view")

def _build_serve_dist():
    """Build serve distribution."""
    subprocess.check_call(["npm", "install"], cwd="./guild/serve")
    subprocess.check_call(["npm", "run", "build"], cwd="./guild/serve")

def _patch_git_obtain():
    """Patch pip's git 'obtain' to download rather than clone.

    pip wants to clone the git repos, which can take a long time. As
    we always use temp dirs for downloads, there no payoff for the
    full clone. This patch downloads and unpacks the revision archive.
    """

    def obtain(self, dest):
        url, rev = self.get_url_rev()
        archive_url = "{}/archive/{}.zip".format(url, rev)
        util.ensure_dir(dest)
        downloaded_file = pip_util.download_url(archive_url, dest)
        zf = zipfile.ZipFile(downloaded_file)
        for name in zf.namelist():
            dest_path = os.path.join(*([dest] + name.split("/")[1:]))
            if name.endswith("/"):
                util.ensure_dir(dest_path)
            else:
                with open(dest_path, "wb") as fdst:
                    fsrc = zf.open(name)
                    shutil.copyfileobj(fsrc, fdst)
    Git.obtain = obtain

_patch_git_obtain()

setup(
    # Setup class config
    cmdclass={"build_py": Build},
    distclass=BinaryDistribution,

    # Attributes from dist-info
    name="guildai",
    version=guild.__version__,
    description=PKG_INFO.get("Summary"),
    install_requires=PKG_INFO.get_all("Requires-Dist"),
    long_description=PKG_INFO.get_payload(),
    url=PKG_INFO.get("Home-page"),
    maintainer=PKG_INFO.get("Author"),
    maintainer_email=PKG_INFO.get("Author-email"),
    entry_points=ENTRY_POINTS,
    classifiers=PKG_INFO.get_all("Classifier"),
    license=PKG_INFO.get("License"),
    keywords=PKG_INFO.get("Keywords"),

    # Package data
    packages=guild_packages(),
    include_package_data=True,

    # Other package info
    zip_safe=False,
    scripts=["./guild/scripts/guild-env"],
)
