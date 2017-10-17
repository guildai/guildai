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

from pkg_resources import PathMetadata
from pkg_resources import Distribution as PkgDist
from setuptools import find_packages, setup
from setuptools.dist import Distribution

import guild

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

class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True

PKG_INFO, ENTRY_POINTS = guild_dist_info()

setup(
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
    distclass=BinaryDistribution,
)
