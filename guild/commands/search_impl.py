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

from __future__ import absolute_import
from __future__ import division

from guild import cli
from guild import namespace
from guild import package
from guild import pip_util

def main(args):
    results = pip_util.search(list(args.terms))
    filtered = _filter_packages(results, args)
    formatted = [_format_package(pkg) for pkg in filtered]
    cli.table(
        formatted,
        cols=["name", "version", "description"],
        sort=["name"])

def _filter_packages(pkgs, args):
    if args.all:
        return pkgs
    return [pkg for pkg in pkgs if package.is_gpkg(pkg["name"])]

def _format_package(pkg):
    return {
        "name": namespace.apply_namespace(pkg["name"]),
        "version": pkg["version"],
        "description": pkg["summary"],
    }
