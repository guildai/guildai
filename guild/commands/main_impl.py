# Copyright 2017-2022 RStudio, PBC
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

import logging
import os

from guild import cli
from guild import config
from guild import log
from guild import util


def main(args):
    _init_logging(args)
    config.set_cwd(_cwd(args))
    config.set_guild_home(_guild_home(args))
    _apply_guild_patch()
    _register_cmd_context_handlers()


def _init_logging(args):
    log_level = args.log_level or logging.INFO
    log.init_logging(log_level)
    log.disable_noisy_loggers(log_level)


def _cwd(args):
    return _validated_dir(args.cwd)


def _guild_home(args):
    return _validated_dir(args.guild_home, abs=True, create=True, guild_nocopy=True)


def _validated_dir(path, abs=False, create=False, guild_nocopy=False):
    path = os.path.expanduser(path)
    if abs:
        path = os.path.abspath(path)
    if not os.path.exists(path):
        if create:
            util.ensure_dir(path)
        else:
            cli.error("directory '%s' does not exist" % path)
    if not os.path.isdir(path):
        cli.error("'%s' is not a directory" % path)
    if guild_nocopy:
        util.ensure_file(os.path.join(path, ".guild-nocopy"))
    return path


def _apply_guild_patch():
    """Look in config cwd for guild_patch.py and load if exists."""
    patch_path = os.path.join(config.cwd(), "guild_patch.py")
    if os.path.exists(patch_path):
        from guild import python_util

        python_util.exec_script(patch_path)


def _register_cmd_context_handlers():
    """Register command context handlers.

    Command context handlers can be used to respond to start and stop
    of Guild commands.

    Currently Guild supports one handler type - socket notification of
    command info. This can be used to monitor Guild commands by
    setting the `GUILD_CMD_NOTIFY_PORT` env var to a port of a socket
    server. See `guild.cmd_notify` for details.
    """
    _maybe_register_cmd_notify()


def _maybe_register_cmd_notify():
    port = _try_cmd_notify_port()
    if port:
        from guild import cmd_notify

        cmd_notify.init_cmd_context_handler(port)


def _try_cmd_notify_port():
    port = os.getenv("GUILD_CMD_NOTIFY_PORT")
    if not port:
        return None
    try:
        return int(port)
    except ValueError as e:
        raise SystemExit(
            "invalid value for GUILD_CMD_NOTIFY_PORT %r: must "
            "be a valid numeric port" % port
        ) from e
