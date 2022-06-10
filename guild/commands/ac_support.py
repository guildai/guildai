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

import os
import pathlib
import re
import subprocess

from guild import util


def ac_filename(ext=None, incomplete=None):
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            return _compgen_filenames("file", ext)
        return _list_dir(os.getcwd(), incomplete, ext=ext)
    return []


def _list_dir(dir, incomplete, filters=None, ext=None):
    """Python based directory listing for completions.

    We use shell functions (e.g. compgen on bash) where possible to
    provide listing. This is for the sake of speed as well as making
    the behavior as close as possible to the user's native
    shell. However, supporting new shells means implementing behavior
    for our !! directives. We provide native Python implementation as
    a fallback where we have not yet implemented handling for our
    directives.
    """
    ext = _ensure_leading_dots(ext)
    if incomplete and os.path.sep in incomplete:
        leading_dir, incomplete = os.path.split(incomplete)
    else:
        leading_dir = ""
    fulldir = os.path.join(dir, leading_dir)

    if not os.path.isdir(fulldir):
        return []

    results = set()

    for path in pathlib.Path(fulldir).iterdir():
        key = str(path.relative_to(dir)) + ("/" if path.is_dir() else "")
        # pylint: disable=too-many-boolean-expressions
        if (
            (not ext or path.suffix in set(ext))
            and path.name not in {".guild", "__pycache__"}
            and (not incomplete or path.name.startswith(incomplete))
            and (not filters or all(filter(str(path)) for filter in filters))
        ):
            results.add(key)
    return util.natsorted(results)


def _ensure_leading_dots(l):
    if not l:
        return l
    return ["." + x if x[:1] != "." else x for x in l]


def ac_dir(incomplete=None):
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            return ["!!dir"]
        return _list_dir(os.getcwd(), incomplete, filters=[os.path.isdir])
    return []


def ac_opnames(names):
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            names = ["!!no-colon-wordbreak"] + names
        return names
    return []


def _compgen_filenames(type, ext):
    if not ext:
        return ["!!%s:*" % type]
    return ["!!%s:*.@(%s)" % (type, "|".join(ext))]


def ac_nospace():
    # TODO: zsh supports this directive, but not the others.
    # We should add proper support for all of them at some point.
    if (
        os.getenv("_GUILD_COMPLETE")
        and _active_shell_supports_directives()
        or _active_shell() == "zsh"
    ):
        return ["!!nospace"]
    return []


def ac_batchfile(ext=None, incomplete=None):
    incomplete = incomplete or ""
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            return _compgen_filenames("batchfile", ext)
        return [
            "@" + str(item)
            for item in _list_dir(os.getcwd(), incomplete.replace("@", ""), ext=ext)
        ]
    return []


def ac_command(incomplete):
    return _gen_ac_command(None, None, incomplete)


def ac_python(incomplete):
    return _gen_ac_command("python*[^-config]", r"^python[^-]*(?!-config)$", incomplete)


def _gen_ac_command(directive_filter, regex_filter, incomplete):
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            if directive_filter:
                return ["!!command:%s" % directive_filter]
            return ["!!command"]

        # TODO: how should we handle this on windows? call out to bash
        #    explicitly? better to avoid explicitly calling sh.
        available_commands = subprocess.check_output(
            [
                "sh",
                "-c",
                "ls $(echo $PATH | tr ':' ' ') | grep -v '/' | grep . | sort | uniq",
            ],
            stderr=subprocess.DEVNULL,
        )
        available_commands = [_.decode() for _ in available_commands.strip().split()]
        if regex_filter:
            filter_re = re.compile(regex_filter)
            available_commands = [
                cmd for cmd in available_commands if filter_re.match(cmd)
            ]
        if incomplete:
            available_commands = [
                cmd for cmd in available_commands if cmd.startswith(incomplete)
            ]
        return available_commands
    return []


def ac_run_dirpath(run_dir, all=False, incomplete=None):
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            if all:
                return ["!!allrundirs:%s" % run_dir]
            return ["!!rundirs:%s" % run_dir]
        filters = [os.path.isdir, lambda x: os.path.isdir(os.path.join(x, ".guild"))]
        if all:
            filters.pop()
        return _list_dir(dir=run_dir, incomplete=incomplete, filters=filters)
    return []


def ac_run_filepath(run_dir, incomplete):
    if os.getenv("_GUILD_COMPLETE"):
        if _active_shell_supports_directives():
            return ["!!runfiles:%s" % run_dir]
        return _list_dir(run_dir, incomplete)
    return []


def ac_safe_apply(ctx, f, args):
    from guild import config

    with config.SetGuildHome(ctx.parent.params.get("guild_home")):
        try:
            return f(*args)
        except (Exception, SystemExit):
            if os.getenv("_GUILD_COMPLETE_DEBUG") == "1":
                raise
            return None


def _active_shell():
    return os.getenv("_GUILD_COMPLETE_SHELL") or util.active_shell()


def _active_shell_supports_directives():
    # TODO: we should maybe register this support in a more dynamic
    # way instead of hard-coding it
    return _active_shell() in {
        "bash",
    }
