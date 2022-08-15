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
import socket

log = logging.getLogger("guild")


class MsgSendError(Exception):
    def __init__(self, error, port):
        super().__init__("Error sending msg to port %i: %s" % (port, error))
        self.error = error
        self.port = port


class CmdContextHandler:

    disabledByError = False

    def __init__(self, port):
        self.port = port

    def on_enter(self, ctx):
        _try_send_msg(_cmd_enter_msg(ctx), self)

    def on_exit(self, ctx, exc_type, *_exc_rest):
        _try_send_msg(_cmd_exit_msg(ctx, exc_type), self)


def _cmd_enter_msg(ctx):
    return _gen_cmd_msg(b"cmd-enter", ctx)


def _cmd_exit_msg(ctx, exc_type):
    if exc_type:
        return _gen_cmd_msg(b"cmd-error", ctx)
    else:
        return _gen_cmd_msg(b"cmd-exit", ctx)


def _gen_cmd_msg(msg_type, ctx):
    return b" ".join([msg_type, _encode_cmd_id(ctx.id)])


def _encode_cmd_id(name):
    return name.encode("utf-8")


def _try_send_msg(msg, handler):
    if handler.disabledByError:
        log.debug(
            "skipping msg %r to notify port %i (notifications "
            "disabled due to previous error)",
            msg,
            handler.port,
        )
        return
    try:
        _send_msg(msg, handler.port)
    except MsgSendError as e:
        _handle_msg_send_error(e, msg, handler)


def _send_msg(msg, port):
    log.debug("connecting to cmd notify port %i", port)
    try:
        sock = socket.create_connection(("*", port))
    except Exception as e:
        raise MsgSendError(e, port)
    else:
        log.debug("sending msg %r to notify port %i", msg, port)
        with sock:
            sock.send(msg)


def _handle_msg_send_error(msgError, msg, handler):
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.exception("sending msg %r to port %i", msg, msgError.port)
    log.error(
        "Error sending command message to port %i: %s\n"
        "Set GUILD_CMD_NOTIFY_PORT to a different port or disable "
        "notifications by running 'unset GUILD_CMD_NOTIFY_PORT'",
        msgError.port,
        msgError.error,
    )
    handler.disabledByError = True


def init_cmd_context_handler(port):
    from guild import click_util

    handler = CmdContextHandler(port)
    click_util.add_cmd_context_handler(handler.on_enter, handler.on_exit)
