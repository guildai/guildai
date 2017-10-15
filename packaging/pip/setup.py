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

import os
import sys

from setuptools import find_packages, setup
from setuptools.dist import Distribution

import guild

class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True

def README():
    path = os.path.join(os.path.dirname(__file__), "README.rst")
    return open(path).read()

def packages():
    return find_packages(exclude=["guild.tests", "guild.tests.*"])

setup(
    name="guildai",
    version=guild.__version__,
    description="The essential TensorFlow developer toolkit",
    install_requires=guild.__requires__,
    long_description=README(),
    url="https://github.com/guildai/guild-python",
    maintainer="Guild AI",
    maintainer_email="packages@guild.ai",
    packages=packages(),
    include_package_data=True,
    zip_safe=False,
    distclass=BinaryDistribution,
    entry_points={
        "console_scripts": [
            "guild=guild.main_bootstrap:main",
        ]
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        # TODO: Operating System :: MacOS
        # TODO: Operating System :: Microsoft :: Windows
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    license="Apache 2.0",
    keywords="guild guildai tensorflow machine learning",
)
