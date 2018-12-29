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

import os
import sys

import setuptools

def main():
    sys.argv = [sys.argv[0], "bdist_wheel", "--universal", "--dist-dir", "."]
    kw = dict(
        name=os.environ["PACKAGE_NAME"],
        version=os.environ["PACKAGE_VERSION"],
        packages=_find_packages(),
        include_package_data=True,
    )
    return setuptools.setup(**kw)

def _find_packages():
    pkgs = setuptools.find_packages()
    if not pkgs:
        _error(
            "cannot find packages in %s\n"
            "Python scripts must be contained in valid Python "
            "packages, which are directories containing __init__.py."
            % os.getcwd())
    return pkgs

def _error(msg):
    sys.stderr.write("Error generating package: ")
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
