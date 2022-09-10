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
    _maybe_debug_listen(args)
    config.set_cwd(_cwd(args))
    config.set_guild_home(_guild_home(args))
    _apply_guild_patch()
    _register_cmd_context_handlers()


def _init_logging(args):
    log_level = args.log_level or logging.INFO
    log.init_logging(log_level)
    log.disable_noisy_loggers(log_level)


def _maybe_debug_listen(args):
    if args.debug_listen:
        _debug_listen(args)


def _debug_listen(args):
    import debugpy

    log = logging.getLogger("guild")
    debugpy.listen(_debug_listen_endpoint(args.debug_listen))
    log.info(f"Debug server listerning on {args.debug_listen}")
    log.info("Waiting for debug client")
    debugpy.wait_for_client()
    log.info("Debug client connected, resuming")


def _debug_listen_endpoint(s):
    parts = s.split(":", 1)
    if len(parts) == 2:
        return (parts[0], _debug_endpoint_port(parts[1]))
    return ("127.0.0.1", _debug_endpoint_port(parts[0]))


def _debug_endpoint_port(s):
    try:
        return int(s)
    except ValueError:
        raise SystemExit(f"invalid value for debug listen PORT {s!r}") from None


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
            cli.error(f"directory '{path}' does not exist")
    if not os.path.isdir(path):
        cli.error(f"'{path}' is not a directory")
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
            f"invalid value for GUILD_CMD_NOTIFY_PORT {port!r}: must "
            "be a valid numeric port"
        ) from e
