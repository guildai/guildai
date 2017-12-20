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

import glob
import os
import sys

from pkg_resources import PathMetadata
from pkg_resources import Distribution as PkgDist
from setuptools import find_packages, setup
from setuptools.dist import Distribution
from setuptools.command.build_py import build_py

import guild
from guild import util
from guild import log

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
    "click": ("guildai/click", "4964698ef8c49f5d27801f1f334397ff834acfbf"),
    "psutil": ("giampaolo/psutil", "release-5.4.2"),
}

class BinaryDistribution(Distribution):

    @staticmethod
    def has_ext_modules():
        return True

class Build(build_py):

    def run(self):
        self.ensure_external()
        build_py.run(self)

    def ensure_external(self):
        for name in EXTERNAL:
            if os.path.exists(self.external_marker(name)):
                continue
            self.install_external(name, EXTERNAL[name])

    @staticmethod
    def external_marker(name):
        return os.path.join(
            "./guild/external",
            ".{}-py{}".format(name, sys.version_info[0]))

    def install_external(self, name, dist_spec):
        with util.TempDir("pip-download-") as tmp:
            wheel_path = self.pip_wheel(name, dist_spec, tmp)
            self.install_external_wheel(wheel_path)
            open(self.external_marker(name), "w").close()

    @staticmethod
    def pip_wheel(name, dist_spec, root):
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
        from pip.commands.wheel import WheelCommand
        cmd = WheelCommand()
        options, cmd_args = cmd.parse_args(args)
        cmd.run(options, cmd_args)
        wheels = glob.glob(os.path.join(wheel_dir, "*.whl"))
        assert len(wheels) == 1, wheels
        return wheels[0]

    @staticmethod
    def install_external_wheel(wheel_path):
        import zipfile
        zf = zipfile.ZipFile(wheel_path)
        util.ensure_dir("./guild/external")
        zf.extractall("./guild/external")

setup(
    # Setup class config
    cmdclass={
        "build_py": Build
    },
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
)
