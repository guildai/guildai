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

import click

from guild import click_util

@click.group("s3-sync", cls=click_util.Group)

def s3_sync():
    """Manage S3 sync service.
    """

@click.command()
@click.option(
    "-f", "--foreground",
    is_flag=True,
    help="Run in the foreground.")

@click_util.use_args

def start(args):
    """Start S3 sync service.
    """
    from . import s3_sync_impl
    s3_sync_impl.start(args)

@click.command()

def stop():
    """Stop S3 sync service.
    """
    from . import s3_sync_impl
    s3_sync_impl.stop()

@click.command()

def status():
    """Show S3 sync service status.
    """
    from . import s3_sync_impl
    s3_sync_impl.status()

s3_sync.add_command(start)
s3_sync.add_command(stop)
s3_sync.add_command(status)
