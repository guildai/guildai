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

# Avoid expensive or one-off imports


def _omit_pycache(path):
    return "__pycache__" not in str(path)


def ac_filename(ext, incomplete):
    if _active_shell_supports_directives():
        return _compgen_filenames("file", ext)
    return _list_dir(
        os.getcwd(),
        filters=[_omit_pycache],
        ext=ext,
        incomplete=incomplete,
    )


def _list_dir(dir, filters=None, ext=None, incomplete=None):
    """Python based directory listing for completions.

    Returns a list of paths for `dir` to include in completion
    results.

    We use shell functions (e.g. compgen on bash) where possible to
    provide listing. This is for the sake of speed as well as making
    the behavior as close as possible to the user's native
    shell. However, supporting new shells means implementing behavior
    for our !! directives. We provide native Python implementation as
    a fallback where we have not yet implemented handling for our
    directives.

    `filters` is a None or a list of functions used to filter (select
    for inclusion) paths by returning True. Each function must accept
    a single argument, which is a pathlib.Path object for the path
    being filtered.  All filters must return True for a path to be
    included in the result.

    `ext` is None or a list of file extensions, not including leading
    dots. If specified, a path is filtered (selected for inclusion) if
    its suffix matches any of the specified extensions. Matching in
    this case is case insensitive.
    """
    import pathlib

    ext = set(_normalize_file_extensions(ext))

    subdir_incomplete, path_incomplete = _split_path_incomplete(incomplete)
    root = pathlib.Path(dir, subdir_incomplete)
    if not os.path.isdir(root):
        return []

    results = set()
    for path in root.iterdir():
        if not _filter_path(path, filters, ext, path_incomplete):
            continue
        results.add(_format_path_for_list(path, dir))
    return _sort_list_dir_result(results)


def _split_path_incomplete(incomplete):
    return os.path.split(incomplete) if incomplete else ("", "")


def _normalize_file_extensions(exts):
    """Normalizes a list of extensions for use in filtering.

    Each extension is returned from `exts` as lower-case and with a
    leading dot. This format can be used to test an lower-case suffix.
    """
    return ["." + ext.lower() for ext in (exts or [])]


def _filter_path(path, filters, normlized_extensions, incomplete):
    if filters and not _apply_path_filters(filters, path):
        return False
    if incomplete and not path.name.startswith(incomplete):
        return False
    if path.is_dir():
        return True
    if normlized_extensions and not path.suffix.lower() in normlized_extensions:
        return False
    return True


def _apply_path_filters(filters, path):
    return all(f(path) for f in filters)


def _format_path_for_list(path, toplevel_dir):
    return str(path.relative_to(toplevel_dir)) + _maybe_trailing_sep(path)


def _maybe_trailing_sep(path):
    return os.path.sep if path.is_dir() else ""


def _sort_list_dir_result(paths):
    """Returns sorted list of paths for a directory listing.

    Entries are ordered alphabetically with directories always occurring
    after non-directories.
    """
    return sorted(paths, key=_list_dir_sort_key)


def _list_dir_sort_key(path):
    return (1, path) if path[-1:] == os.path.sep else (0, path)


def ac_dir(incomplete):
    if _active_shell_supports_directives():
        return ["!!dir"]
    return _list_dir(
        os.getcwd(), filters=[os.path.isdir, _omit_pycache], incomplete=incomplete
    )


def ac_no_colon_wordbreak(values, incomplete):
    values = _values_for_incomplete(incomplete, values)
    if _active_shell_supports_directives():
        return ["!!no-colon-wordbreak"] + values
    return values


def _values_for_incomplete(incomplete, values):
    if not incomplete:
        return values
    return [s for s in values if s.startswith(incomplete)]


def _compgen_filenames(type, ext):
    if not ext:
        return ["!!%s:*" % type]
    return ["!!%s:*.@(%s)" % (type, "|".join(ext))]


def ac_nospace(values, incomplete):
    values = _values_for_incomplete(incomplete, values)
    if _active_shell_supports_nospace():
        return ["!!nospace"] + values
    return values


def _active_shell_supports_nospace():
    # zsh is a one-off shell that supports the nospace directive but
    # otherwise doesn't support directives. See
    # (../completions/zsh-guild for details).
    return _active_shell_supports_directives() or _active_shell() == "zsh"


def ac_batchfile(ext, incomplete):
    if _active_shell_supports_directives():
        return _compgen_filenames("batchfile", ext)
    batchfile_paths = _list_dir(
        os.getcwd(),
        ext=ext,
        incomplete=_strip_batch_prefix(incomplete),
        filters=[_omit_pycache],
    )
    return [_apply_batch_prefix(path) for path in batchfile_paths]


def _strip_batch_prefix(s):
    return s[1:] if s and s[:1] == "@" else s


def _apply_batch_prefix(s):
    return "@" + s


def ac_command(incomplete):
    return _gen_ac_command(None, None, incomplete)


def ac_python(incomplete):
    return _gen_ac_command(
        "python*[^-config]",
        r"^python[^-]*(?!-config)$",
        incomplete,
    )


def _gen_ac_command(directive_filter, regex_filter, incomplete):
    import re
    import subprocess

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
        available_commands = [cmd for cmd in available_commands if filter_re.match(cmd)]
    return _values_for_incomplete(incomplete, available_commands)


def ac_run_filepath(run_dir, incomplete):
    if _active_shell_supports_directives():
        return ["!!runfiles:%s" % run_dir]
    return _list_dir(
        run_dir, filters=[_run_filepath_filter, _omit_pycache], incomplete=incomplete
    )


def _run_filepath_filter(p):
    """Filter used with _list_dir to remove `.guild` from completions."""
    return p.name != ".guild"


def ac_safe_apply(f, args):
    try:
        return f(*args)
    except (Exception, SystemExit):
        import logging

        if logging.getLogger("guild").getEffectiveLevel() <= logging.DEBUG:
            raise
        return None


def _active_shell():
    from guild import util

    return os.getenv("_GUILD_COMPLETE_SHELL") or util.active_shell()


def _active_shell_supports_directives():
    return _active_shell() in ("bash",)


def ac_assignments(key, values, value_incomplete):
    values = _values_for_incomplete(value_incomplete, values)
    if not _active_shell_requires_full_assign():
        return values
    return [f"{key}={val}" for val in values]


def _active_shell_requires_full_assign():
    return _active_shell() != "bash"
