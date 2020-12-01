# Copyright 2017-2020 TensorHub, Inc.
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

import click

from guild import click_util


def _ac_package(incomplete, **_kw):
    from . import packages_impl

    return sorted(
        [
            pkg.project_name
            for pkg in packages_impl.packages()
            if pkg.project_name.startswith(incomplete)
        ]
    )


def delete_params(fn):
    click_util.append_params(
        fn,
        [
            click.Argument(
                ("packages",),
                metavar="PACKAGE...",
                nargs=-1,
                required=True,
                autocompletion=_ac_package,
            ),
            click.Option(
                ("-y", "--yes"),
                help="Do not prompt before uninstalling.",
                is_flag=True,
            ),
        ],
    )
    return fn


@click.command("delete, rm")
@delete_params
@click_util.use_args
def delete_packages(args):
    """Uninstall one or more packages."""
    from . import packages_impl

    packages_impl.uninstall_packages(args)
