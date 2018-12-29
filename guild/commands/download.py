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

import click

from guild import click_util

@click.command()
@click.argument("url")

@click_util.use_args

def download(args):
    """Download a file resource.

    `URL` is downloaded as a Guild resource in the current
    environment. Once downloaded, it is available as a resource using
    the same URL.

    **NOTE:** When used in a Guild file, `URL` must be specified
    exactly as used in this command. Guild will treat any changes as a
    different resource.

    **IMPORTANT:** Independently verify SHA 256 digests for downloaded
    resources, especially those that will be executed, including
    Python libraries.

    Existing resources are not re-downloaded. To force a resource to
    be re-downloaded, delete the resource file and run `download`
    again.

    The commands prints the SHA 256 digest with the full path to the
    downloaded file.

    """

    from . import download_impl
    download_impl.main(args)
