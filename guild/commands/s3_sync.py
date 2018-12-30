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

@click.group("s3-sync", cls=click_util.Group)

def s3_sync():
    """Manage S3 sync service.
    """

@click.command()
@click.argument("uri", metavar="URI")
@click.option(
    "-i", "--sync-interval",
    default=60,
    type=click.IntRange(5, None),
    help=(
        "Maximum interval between synchronization attempts "
        "(default is 60)."))
@click.option(
    "-m", "--log-max-size", metavar="MB",
    default=100,
    type=click.IntRange(1, None),
    help="Maximum log size in megabytes (default is 100).")
@click.option(
    "-b", "--log-backups", metavar="N",
    default=5,
    type=click.IntRange(0, None),
    help=(
        "Number of log backups to maintain when run as a service "
        "(default is 5)."))
@click.option(
    "-f", "--foreground",
    is_flag=True,
    help="Run in the foreground.")

@click_util.use_args

def start(args):
    """Start S3 sync service.

    The S3 sync service synchronizes runs with S3 location
    `URI`. `URI` must be in the format ``s3://BUCKET[/PATH]`` where
    ``BUCKET`` is a writable S3 bucket and ``PATH`` is an optional
    path within the bucket.

    Credentials must be provided using ``AWS_ACCESS_KEY_ID`` and
    ``AWS_SECRET_ACCESS_KEY`` environment variables.

    The bucket region may be specified using `--region` or using
    ``AWS_DEFAULT_REGION`` environment variable.

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
