# Copyright 2017-2022 TensorHub, Inc.
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

import os
import platform
import subprocess
import sys

sys.path.insert(0, "./guild/external")

from pkg_resources import Distribution as PkgDist
from pkg_resources import PathMetadata
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py

import guild

from guild import log

log.init_logging()

GUILD_DIST_BASENAME = "guildai.dist-info"

if platform.system() == "Windows":
    NPM_CMD = "npm.cmd"
else:
    NPM_CMD = "npm"


def guild_dist_info():
    metadata = PathMetadata(".", GUILD_DIST_BASENAME)
    dist = PkgDist.from_filename(GUILD_DIST_BASENAME, metadata)
    assert dist.project_name == "guildai", dist
    entry_points = {
        group: [str(ep) for ep in eps.values()]
        for group, eps in dist.get_entry_map().items()
    }
    return dist._parsed_pkg_info, entry_points


def guild_packages():
    return find_packages(exclude=["guild.tests", "guild.tests.*"])


PKG_INFO, ENTRY_POINTS = guild_dist_info()


class Build(build_py):
    """Extension of default build with additional pre-processing.

    In preparation for setuptool's default build, we perform these
    additional pre-processing steps:

    - Ensure external dependencies
    - Build view distribution

    See MANIFEST.in for a complete list of data files includes in the
    Guild distribution.
    """

    def run(self):
        _validate_env()
        if os.getenv("SKIP_VIEW") != "1":
            _build_view_dist()
        build_py.run(self)


def _validate_env():
    try:
        subprocess.check_output([NPM_CMD, "--version"])
    except OSError as e:
        raise SystemExit("error checking npm: %s" % e)


def _build_view_dist():
    """Build view distribution."""
    # Switch to opt out of npm builds driven by npm issues on
    # Appveyor. Workaround is to store developer-built view app in
    # source and use as fallback on platforms struggling to build with
    # npm.
    if os.getenv("SKIP_NPM") != "1":
        subprocess.check_call([NPM_CMD, "install"], cwd="./guild/view")
        subprocess.check_call([NPM_CMD, "run", "build"], cwd="./guild/view")


setup(
    # Setup class config
    cmdclass={"build_py": Build},
    # Attributes from dist-info
    name="guildai",
    version=guild.__version__,
    description=PKG_INFO.get("Summary"),
    install_requires=PKG_INFO.get_all("Requires-Dist"),
    long_description=PKG_INFO.get_payload(),
    long_description_content_type="text/markdown",
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
