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

from guild import cli
from guild import click_util


def _ac_remote(incomplete, **_kw):
    from guild import config

    remotes = config.user_config().get("remotes", {})
    return sorted([r for r in remotes if r.startswith(incomplete)])


def remote_arg(fn):
    """`REMOTE` is the name of a configured remote. Use ``guild remotes``
    to list available remotes.

    For information on configuring remotes, see ``guild remotes
    --help``.

    """
    click_util.append_params(
        fn, [click.Argument(("remote",), autocompletion=_ac_remote)]
    )
    return fn


def remote_option(help):
    """`REMOTE` is the name of a configured remote. Use ``guild remotes``
    to list available remotes.

    For information on configuring remotes, see ``guild remotes
    --help``.

    """
    assert isinstance(help, str), "@remote_option must be called with help"

    def wrapper(fn):
        click_util.append_params(
            fn,
            [
                click.Option(
                    ("-r", "--remote"),
                    metavar="REMOTE",
                    help=help,
                    autocompletion=_ac_remote,
                )
            ],
        )
        return fn

    return wrapper


def remotes():
    """### Remotes

    Remotes are non-local systems that Guild can interact with. They
    are defined in ``~/.guild/config.yml`` under the ``remotes``
    section.

    For a list of supported remotes, see https://guild.ai/remotes/.

    """


def remote_for_args(args):
    from guild import remote as remotelib  # expensive

    assert args.remote, args

    try:
        return remotelib.for_name(args.remote)
    except remotelib.NoSuchRemote:
        inline_remote = _try_inline_remote(args.remote)
        if inline_remote:
            return inline_remote
        cli.error(
            "remote '%s' is not defined\n"
            "Show remotes by running 'guild remotes' or "
            "'guild remotes --help' for more information." % args.remote
        )
    except remotelib.UnsupportedRemoteType as e:
        cli.error(
            "remote '%s' in ~/.guild/config.yml has unsupported "
            "type: %s" % (args.remote, e.args[0])
        )
    except remotelib.MissingRequiredConfig as e:
        cli.error(
            "remote '%s' in ~/.guild/config.yml is missing required "
            "config: %s" % (args.remote, e.args[0])
        )
    except remotelib.ConfigError as e:
        cli.error(
            "remote '%s' in ~/.guild/config.yml has a configuration "
            "error: %s" % (args.remote, e.args[0])
        )


def _try_inline_remote(remote_arg):
    from guild import remote as remotelib  # expensive

    try:
        return remotelib.for_spec(remote_arg)
    except remotelib.InvalidRemoteSpec as e:
        cli.error(e.args[0])
    except remotelib.RemoteForSpecNotImplemented as e:
        cli.error("remote type '%s' does not support inline specifications" % e.args[0])
    except remotelib.UnsupportedRemoteType as e:
        cli.error("unknown remote type '%s'" % e.args[0])
