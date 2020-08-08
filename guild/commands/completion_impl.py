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

import glob
import logging
import os
import shutil
import sys

import guild

from guild import cli
from guild import config
from guild import util

log = logging.getLogger("guild")


DEFAULT_SHELL = "bash"
SHELL_INIT_BACKUP_SUFFIX_PATTERN = ".guild-backup.{n}"


def main(args):
    shell = args.shell or _current_shell()
    script = _completion_script(shell)
    if args.install:
        _install_completion_script(shell, script, args)
    else:
        sys.stdout.write(script)
        sys.stdout.write("\n")


def _current_shell():
    shell_env = os.getenv("SHELL")
    if not shell_env or "bash" in shell_env:
        return DEFAULT_SHELL
    elif "zsh" in shell_env:
        return "zsh"
    elif "fish" in shell_env:
        return "fish"
    else:
        log.warning("unknown shell '%s', assuming %s", shell_env, DEFAULT_SHELL)
        return DEFAULT_SHELL


def _completion_script(shell):
    path = os.path.join(_completions_dir(), "%s-guild" % shell)
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.debug("completion script path for %s: %s", shell, path)
    if not os.path.exists(path):
        cli.error("unsupported shell: %s" % shell)
    return open(path, "r").read()


def _completions_dir():
    return os.path.join(os.path.dirname(guild.__file__), "completions")


def _install_completion_script(shell, script, args):
    script_path = _write_completion_script_to_user_config(shell, script)
    _install_completion_script_to_shell_init(shell, script_path, args)


def _write_completion_script_to_user_config(shell, script):
    path = os.path.join(config.user_config_home(), "%s_completion" % shell)
    cli.out("Writing completion script to %s" % util.format_dir(path), err=True)
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(script)
        f.write("\n")
    return path


def _install_completion_script_to_shell_init(shell, script_path, args):
    if shell == "bash":
        _install_completion_script_to_bash_init(script_path, args)
    elif shell == "zsh":
        _install_completion_script_to_zsh_init(script_path, args)
    elif shell == "fish":
        _install_completion_script_to_fish_init(script_path, args)
    else:
        assert False, shell


def _install_completion_script_to_bash_init(script_path, args):
    init_script = args.shell_init or "~/.bashrc"
    user_dir_script_path = _user_dir_path(script_path)
    sentinel = ". %s" % user_dir_script_path
    lines = [
        "[ -s {script} ] && . {script}  # Enable completion for guild".format(
            script=user_dir_script_path
        )
    ]
    _gen_install_completion_script_to_init(init_script, sentinel, lines)


def _install_completion_script_to_zsh_init(script_path, args):
    init_script = args.shell_init or "~/.zshrc"
    user_dir_script_path = _user_dir_path(script_path)
    sentinel = ". %s" % user_dir_script_path
    lines = [
        "[[ -s {script} ]] && . {script}  # Enable completion for guild".format(
            script=user_dir_script_path
        )
    ]
    _gen_install_completion_script_to_init(init_script, sentinel, lines)


def _install_completion_script_to_fish_init(script_path, args):
    init_script = args.shell_init or "~/.config/fish/completions/guild.fish"
    user_dir_script_path = _user_dir_path(script_path)
    sentinel = ". %s" % user_dir_script_path
    lines = ["test -s {script} ;and . {script}".format(script=user_dir_script_path)]
    _gen_install_completion_script_to_init(init_script, sentinel, lines, backup=False)


def _gen_install_completion_script_to_init(init_script, sentinel, lines, backup=True):
    init_script = os.path.expanduser(init_script)
    _check_init_script(init_script, sentinel)
    if backup:
        _backup_init_script(init_script)
    _append_to_init_script(init_script, lines)
    cli.out(
        "Guild command completion is installed - changes will take effect the next "
        "time you open a terminal session"
    )


def _check_init_script(path, sentinel):
    if not os.path.exists(path):
        return
    lines = open(path).readlines()
    for i, line in enumerate(lines):
        if sentinel in line:
            cli.out(
                "Guild completion is already installed in %s on line %i:\n  %s"
                % (util.format_dir(path), i + 1, line.rstrip()),
                err=True,
            )
            raise SystemExit(0)


def _backup_init_script(init_script):
    if os.path.exists(init_script):
        backup = _init_script_backup(init_script)
        cli.out(
            "Backing up %s to %s"
            % (util.format_dir(init_script), util.format_dir(backup)),
            err=True,
        )
        shutil.copy(init_script, backup)


def _init_script_backup(path):
    return path + _next_backup_suffix(path)


def _next_backup_suffix(dir):
    cur = 0
    for path in glob.glob(dir + SHELL_INIT_BACKUP_SUFFIX_PATTERN.format(n="*")):
        try:
            n = int(os.path.splitext(path)[1][1:])
        except ValueError:
            pass
        else:
            cur = max(n, cur)
    return SHELL_INIT_BACKUP_SUFFIX_PATTERN.format(n=cur + 1)


def _append_to_init_script(init_script, lines):
    cli.out(
        "Updating %s to support Guild command completion"
        % util.format_dir(init_script),
        err=True,
    )
    util.ensure_dir(os.path.dirname(init_script))
    exists = os.path.exists(init_script)
    with open(init_script, "a") as f:
        if exists:
            f.write(os.linesep)
        for line in lines:
            f.write(line)
            f.write(os.linesep)


def _user_dir_path(path):
    return util.format_user_dir(os.path.abspath(path))
