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

from guild import cli
from guild import namespace
from guild import pip_util

def main(args):
    formatted = [_format_package(pkg) for pkg in _search(args)]
    cli.table(
        formatted,
        cols=["name", "version", "description"],
        sort=["name"])

def _search(args):
    spec, operator = _search_spec(args)
    return pip_util.search(spec, operator)

def _search_spec(args):
    terms = list(args.terms)
    if args.all:
        return {
            "name": terms,
            "summary": terms
        }, "or"
    else:
        return {
            "description": terms,
            "keywords": ["gpkg"]
        }, "and"

def _format_package(pkg):
    return {
        "name": namespace.apply_namespace(pkg["name"]),
        "version": pkg["version"],
        "description": _format_summary(pkg["summary"]),
    }

def _format_summary(s):
    return s.replace(" (Guild AI)", "")
