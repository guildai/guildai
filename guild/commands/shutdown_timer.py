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

@click.group("shutdown-timer", cls=click_util.Group)

def shutdown_timer():
    """Manager shutdown timer.
    """

@click.command()
@click.option(
    "-t", "--timeout", metavar="MINUTES",
    default=60,
    help="Shutdown timeout in minutes (default is 60).")
@click.option(
    "-s", "--su",
    is_flag=True,
    help="Run shutdown command as privileged user.")
@click.option(
    "-f", "--foreground",
    is_flag=True,
    help="Run in the foreground.")
@click.option(
    "-g", "--grace-period",
    type=click.IntRange(0, None),
    default=1,
    help="Number of minutes used in shutdown command (default 1).")
@click.option(
    "-d", "--dont-shutdown",
    is_flag=True,
    help="Don't issue a system shutdown command (use for testing).")

@click_util.use_args

def start(args):
    """Start shutdown timer.
    """
    from . import shutdown_timer_impl
    shutdown_timer_impl.start(args)

@click.command()

def stop():
    """Stop shutdown timer.
    """
    from . import shutdown_timer_impl
    shutdown_timer_impl.stop()

@click.command()

def status():
    """Show shutdown timer status.
    """
    from . import shutdown_timer_impl
    shutdown_timer_impl.status()

shutdown_timer.add_command(start)
shutdown_timer.add_command(stop)
shutdown_timer.add_command(status)
