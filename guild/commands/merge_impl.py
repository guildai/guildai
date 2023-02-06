# Copyright 2017-2023 Posit Software, PBC
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

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import exit_code
from guild import run_merge
from guild import run_util
from guild import util
from guild import vcs_util

from . import runs_impl


class SystemExitWithDetail(Exception):
    """Wrapper for SystemExit that includes additional details.

    The merge implementation makes use of SystemExit to terminate the
    process for various reasons. A wrapper is used to convey
    additional details about a system exit that can be used by an API
    (e.g. `guild.commands.merge_api`).

    A caller who's interested in system exit details can call
    `main_with_system_exit_detail` below and should catch
    `SystemExitWithDetail` to get details about a system exit. Note
    the caller must handle the system exit if needed.

    For detail types, see `XxxDetail` classes below.
    """

    def __init__(self, code, detail):
        super().__init__(code, detail)
        self.code = code
        self.detail = detail


class ReplacementPathsDetail:
    def __init__(self, paths):
        self.paths = paths


class UnstagedPathsDetail:
    def __init__(self, paths):
        self.paths = paths


class NothingToCopyDetail:
    pass


class PreviewMergeDetail:
    def __init__(self, merge):
        self.merge = merge


class AbortedDetail:
    pass


def main(args, ctx):
    try:
        main_with_system_exit_detail(args, ctx)
    except SystemExitWithDetail as e:
        raise SystemExit(e.code) from e


def main_with_system_exit_detail(args, ctx):
    _check_args(args, ctx)
    _apply_sourcecode_arg(args)
    run = runs_impl.one_run(args, ctx)
    target_dir = args.target_dir or _checked_cwd(run, ctx)
    merge = _init_run_merge(run, target_dir, args)
    _check_replace(merge, args)
    _check_nothing_to_copy(merge, args, ctx)
    _maybe_preview_merge(merge, args)
    run_merge.apply_run_merge(merge, _on_merge_copy)


def _check_args(args, ctx):
    cmd_impl_support.check_incompatible_args(
        [
            ("replace", "no_replace"),
            ("sourcecode", "skip_sourcecode"),
        ],
        args,
        ctx,
    )


def _apply_sourcecode_arg(args):
    if args.sourcecode:
        args.skip_deps = True


def _init_run_merge(run, target_dir, args):
    try:
        return run_merge.init_run_merge(
            run,
            target_dir,
            copy_all=args.all,
            skip_sourcecode=args.skip_sourcecode,
            skip_deps=args.skip_deps,
            exclude=args.exclude,
            prefer_nonsource=True,
        )
    except run_merge.MergeError as e:
        cli.error(e)


def _checked_cwd(run, ctx):
    """Returns cwd if it's the same as the run's project directory.

    This serves as a safeguard to prevent accidentally merging into an
    unintended target directory. The user is asked to skip this
    check by including --target-dir in the command.
    """
    _checked_cwd_run_pkg_type(run, ctx)
    project_dir = _run_project_dir(run)
    cwd = config.cwd()
    _checked_cwd_matches_project_dir(cwd, project_dir, run, ctx)
    return cwd


def _checked_cwd_run_pkg_type(run, ctx):
    if run.opref.pkg_type not in ("guildfile", "script"):
        cli.error(
            f"run {run.id} does not originate from a project - cannot merge to the "
            "current directory by default\nUse --target-dir to skip this "
            f"check or try '{ctx.command_path} --help' for more information."
        )


def _run_project_dir(run):
    project_dir = run_util.run_project_dir(run)
    if not project_dir:
        cli.error(
            f"unexpected missing project directory for run {run.id} ({run.opref})\n"
            "Skip this check by using --target-dir"
        )
    return project_dir


def _checked_cwd_matches_project_dir(cwd, project_dir, run, ctx):
    if not util.compare_paths(cwd, project_dir):
        fmt_project_dir = util.format_dir(project_dir)
        cli.error(
            f"run {run.id} was created from a different project ({fmt_project_dir}) - "
            "cannot merge to the current directory by default\nUse '--target-dir .' "
            f"to override this check or try '{ctx.command_path} --help' for more "
            "information."
        )


def _check_replace(merge, args):
    """Checks for replacement of files in a target dir.

    Check is disabled if --replace is specified.
    """
    if args.replace or not os.path.exists(merge.target_dir):
        return
    if args.no_replace:
        _fail_if_replacing(merge)
        return
    _try_vcs_status_check_replace(merge)


def _fail_if_replacing(merge):
    replacing = _merge_replacing_files(merge)
    if replacing:
        _replacing_error(replacing, merge)


def _merge_replacing_files(merge):
    return {
        mf.target_path
        for mf in merge.to_copy
        if os.path.exists(os.path.join(merge.target_dir, mf.target_path))
    }


def _replacing_error(target_paths, merge):
    target_dir_desc = cmd_impl_support.cwd_desc(merge.target_dir)
    cli.out(
        f"guild: files in {target_dir_desc} would be replaced:",
        err=True,
    )
    data = [{"path": path} for path in sorted(target_paths)]
    cli.table(data, ["path"], indent=2, err=True)
    cli.out("Use --replace to skip this check.", err=True)
    raise SystemExitWithDetail(1, ReplacementPathsDetail(target_paths))


def _try_vcs_status_check_replace(merge):
    """Tries to apply a VCS check for replacement of files in target dir.

    If target dir is managed by a supported VCS, performs a
    VCS-specific replacement check. See `_check_vcs_status` for
    VCS-specific logic.

    If target dir is not managed by a known VCS, performs the default
    replacement check. See `_fail_if_replacing` for this behavior.
    """
    try:
        vcs_status = vcs_util.status(merge.target_dir)
    except vcs_util.UnsupportedRepo:
        _fail_if_replacing(merge)
    else:
        _check_vcs_status(vcs_status, merge)


def _check_vcs_status(vcs_status, merge):
    """Checks for replacement status in a VCS managed dir.

    `vcs_status` is the result of `vcs_util.status()` for the target
    directory.

    The rules applied are as follows:

    - If there are any non-source to be replaced, treats all replaced
      files as a non-source replace and uses the same message as if
      the project was not VCS managed.

    - If all of the files to be replaced are unstaged source code
      files, shows a message asking user to stage the changes or to
      override with the '--replace' option.

    - If all of the files to be replaced are staged source code
      files, does nothing. This allows the merge to continue under the
      assumption that any replaced files can be recovered from the
      VCS.
    """
    all_source = set(vcs_util.ls_files(merge.target_dir))
    unstaged = _unstaged_source(vcs_status, all_source)
    unstaged_replacing = _unstaged_replacing(unstaged, merge)
    all_replacing = _merge_replacing_files(merge)
    nonsource_replacing = all_replacing - all_source
    if nonsource_replacing:
        _replacing_error(all_replacing, merge)
    elif unstaged_replacing:
        _replace_unstaged_error(unstaged_replacing, merge)


def _unstaged_source(vcs_status, vcs_files):
    return [path for path in vcs_files if _is_unstaged(path, vcs_status)]


def _is_unstaged(vcs_path, vcs_status):
    """Returns True if `vcs_path` (a string) is unstaged in `vcs_status`.

    `vcs_status` is the result of `vcs_util.status()` for the parent
    directory of `vcs_path`.

    `vcs_path` must be managed by the VCS associated with
    `vcs_status`.

    If `vcs_path` is not in `vcs_status`, returns False.
    """
    try:
        path_vcs_status = next(
            filter(lambda fs: vcs_path.startswith(fs.path), vcs_status)
        )
    except StopIteration:
        return False
    else:
        return _is_vcs_file_status_unstaged(path_vcs_status)


def _is_vcs_file_status_unstaged(file_status):
    """Returns True if file status is unstage.

    Staged status is determined by the second position of
    `file_status.stats` code. See `guild.vcs_util.FileStatus` for
    details.
    """
    return file_status.status[1] != "_"


def _unstaged_replacing(unstaged, merge):
    return {mf.target_path for mf in merge.to_copy if mf.target_path in unstaged}


def _replace_unstaged_error(target_paths, merge):
    target_dir_desc = cmd_impl_support.cwd_desc(merge.target_dir)
    cli.out(
        f"guild: files in {target_dir_desc} have unstaged changes:",
        err=True,
    )
    data = [{"path": path} for path in sorted(target_paths)]
    cli.table(data, ["path"], indent=2, err=True)
    cli.out(
        "Stage or stash these changes or use --replace to skip this check.",
        err=True,
    )
    raise SystemExitWithDetail(1, UnstagedPathsDetail(target_paths))


def _check_nothing_to_copy(merge, args, ctx):
    if merge.to_copy or args.preview:
        return
    cli.out("Nothing to copy for the following run:", err=True)
    _preview_merge_run(merge)
    cli.out(
        f"Try '{ctx.command_path} --preview' for a list of skipped files.", err=True
    )
    raise SystemExitWithDetail(0, NothingToCopyDetail())


def _maybe_preview_merge(merge, args):
    if not args.preview and args.yes:
        return
    _preview_merge(merge, args.preview)
    if args.preview:
        raise SystemExitWithDetail(0, PreviewMergeDetail(merge))
    if not cli.confirm("Continue (y/N)?", False):
        raise SystemExitWithDetail(exit_code.ABORTED, AbortedDetail())


def _preview_merge(merge, preview_only):
    _preview_merge_header(merge, preview_only)
    _preview_merge_run(merge)
    _preview_merge_copy_files(merge)
    _preview_merge_skipped_files(merge, preview_only)


def _preview_merge_header(merge, preview_only):
    target_dir_desc = cmd_impl_support.cwd_desc(merge.target_dir)
    if preview_only:
        cli.out(
            f"Merge will copy files from the following run to {target_dir_desc}:",
            err=True,
        )
    else:
        cli.out(
            f"You are about to copy files from the following run to {target_dir_desc}:",
            err=True,
        )


def _preview_merge_run(merge):
    data = runs_impl.format_runs([merge.run])
    cols = [
        "short_index",
        "op_desc",
        "started",
        "status",
        "label",
    ]
    cli.table(data, cols, indent=2, err=True)


def _preview_merge_copy_files(merge):
    cli.out("Files:", err=True)
    if not merge.to_copy:
        cli.out("  nothing to copy", err=True)
    data = _format_merge_copy_files(_sorted_merge_copy_files(merge))
    cli.table(data, cols=["target_path"], indent=2, err=True)


def _sorted_merge_copy_files(merge):
    return sorted(merge.to_copy, key=lambda cf: cf.target_path)


def _format_merge_copy_files(to_copy):
    return [
        {
            "run_path": cf.run_path,
            "target_path": cf.target_path,
        }
        for cf in to_copy
    ]


def _preview_merge_skipped_files(merge, preview_only):
    if not merge.to_skip:
        return
    if preview_only:
        _preview_skipped_files_full(merge)
    else:
        _preview_skipped_files_summary(merge)


def _preview_skipped_files_full(merge):
    cli.out(cli.style("Skipped:", dim=True), err=True)
    data = _format_merge_skip_files(_sorted_merge_skip_files(merge))
    cli.table(data, cols=["path", "reason"], indent=2, err=True, dim=True)


def _sorted_merge_skip_files(merge):
    return sorted(merge.to_skip, key=_skip_file_path)


def _skip_file_path(sf):
    """Returns the path used for a skipped file.

    If a skipped file has a target path, it's used as the path,
    otherwise the file run path is used. A skipped file does not have
    a target path when it does not originate from a project
    directory. This may be because it's a resolved dependency source
    from a remote file or from an unpacked archive.
    """
    return sf.target_path or sf.run_path


def _format_merge_skip_files(to_skip):
    return [
        {
            "path": _skip_file_path(sf),
            "reason": cli.style(_skip_file_reason(sf), italic=True),
        }
        for sf in to_skip
    ]


def _skip_file_reason(sf):
    code = sf.reason
    if code == "?":
        if sf.file_type == "o":
            return "non-project file"
        return f"unknown (type={sf.file_type})"
    if code == "u":
        return "unchanged"
    if code == "npd":
        return "non-project dependency"
    if code == "d":
        return "skipped dependency"
    if code == "s":
        return "skipped source code"
    if code == "x":
        return "excluded"
    return f"unknown (code={code})"


def _preview_skipped_files_summary(merge):
    len_skipped = len(merge.to_skip)
    files_desc = "1 file" if len_skipped == 1 else f"{len_skipped} files"
    cli.out(
        cli.style(
            f"{files_desc} will not be copied (use --preview to show the full list)",
            dim=True,
        ),
        err=True,
    )


def _on_merge_copy(_merge, copy_file, _src, _dest):
    cli.out(f"Copying {copy_file.target_path}", err=True)
