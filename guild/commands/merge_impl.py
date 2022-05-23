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
from guild import cmd_impl_support
from guild import config
from guild import exit_code
from guild import run_merge
from guild import run_util
from guild import util
from guild import vcs_util

from . import runs_impl


log = logging.getLogger("guild")


def main(args, ctx):
    _check_args(args, ctx)
    _apply_sourcecode_arg(args)
    run = runs_impl.one_run(args, ctx)
    merge = _init_run_merge(run, args)
    target_dir = args.target_dir or _checked_cwd(run, ctx)
    _check_replace(merge, target_dir, args)
    _maybe_preview_merge(merge, target_dir, args)
    run_merge.apply_run_merge(merge, target_dir, _on_merge_copy)


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
        args.skip_generated = True


def _init_run_merge(run, args):
    try:
        return run_merge.RunMerge(
            run,
            skip_sourcecode=args.skip_sourcecode,
            skip_deps=args.skip_deps,
            skip_generated=args.skip_generated,
            exclude=args.exclude,
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
            "This may be a bug in Guild - please report to "
            "https://github.com/guildai/guildai/issues\n"
            "Skip this check by using --target-dir"
        )
    return project_dir


def _checked_cwd_matches_project_dir(cwd, project_dir, run, ctx):
    if not util.compare_paths(cwd, project_dir):
        fmt_project_dir = util.format_dir(project_dir)
        cli.error(
            f"run {run.id} originates from a different directory ({fmt_project_dir}) - "
            "cannot merge to the current directory by default\nUse --target-dir "
            f"to override this check or try '{ctx.command_path} --help' for more "
            "information."
        )


def _check_replace(merge, target_dir, args):
    """Checks for replacement of files in a target dir.

    Check is disabled if --replace is specified.
    """
    if args.replace or not os.path.exists(target_dir):
        return
    if args.no_replace:
        _fail_if_replacing(merge, target_dir)
        return
    _try_vcs_status_check_replace(merge, target_dir)


def _fail_if_replacing(merge, target_dir):
    replacing = _merge_replacing_files(merge, target_dir)
    if replacing:
        _replacing_error(replacing, target_dir)


def _merge_replacing_files(merge, target_dir):
    return {
        mf.target_path
        for mf in merge.files
        if os.path.exists(os.path.join(target_dir, mf.target_path))
    }


def _replacing_error(target_paths, target_dir):
    target_dir_desc = cmd_impl_support.cwd_desc(target_dir)
    cli.out(
        f"guild: files in {target_dir_desc} would be replaced:",
        err=True,
    )
    data = [{"path": path} for path in sorted(target_paths)]
    cli.table(data, ["path"], indent=2, err=True)
    cli.out("Use --replace to skip this check.", err=True)
    raise SystemExit()


def _try_vcs_status_check_replace(merge, target_dir):
    """Tries to apply a VCS check for replacement of files in target dir.

    If target dir is managed by a supported VCS, performs a
    VCS-specific replacement check. See `_check_vcs_status` for
    VCS-specific logic.

    If target dir is not managed by a known VCS, performs the default
    replacement check. See `_fail_if_replacing` for this behavior.
    """
    try:
        vcs_status = vcs_util.status(target_dir)
    except vcs_util.UnsupportedRepo:
        _fail_if_replacing(merge, target_dir)
    else:
        _check_vcs_status(vcs_status, merge, target_dir)


def _check_vcs_status(vcs_status, merge, target_dir):
    """Checks for replacement status in a VCS managed dir.

    The rules applied are as follows:

    - If there are any non-source to be replaced, treats all replaced
      files as a non-source replace and uses the same message as if
      the project was not VCS managed.

    - If all of the files to be replaced are uncommitted source code
      files, shows a message asking user to commit the changes or to
      override with the '--replace' option.

    - If all of the files to be replaced are committed source code
      files, does nothing. This allows the merge to continue under the
      assumption that any replaced files can be recovered from the
      VCS.

    """
    all_source = set(vcs_util.ls_files(target_dir))
    uncommitted = _uncommitted_source(vcs_status, all_source)
    uncommitted_replacing = _uncommitted_replacing(uncommitted, merge)
    all_replacing = _merge_replacing_files(merge, target_dir)
    nonsource_replacing = all_replacing - all_source
    if nonsource_replacing:
        _replacing_error(all_replacing, target_dir)
    elif uncommitted_replacing:
        _replace_uncommitted_error(uncommitted_replacing, target_dir)


def _uncommitted_source(vcs_status, vcs_files):
    return [path for path in vcs_files if _in_vcs_status(path, vcs_status)]


def _in_vcs_status(path, vcs_status):
    return any(path.startswith(f.path) for f in vcs_status)


def _uncommitted_replacing(uncommitted, merge):
    return {mf.target_path for mf in merge.files if mf.target_path in uncommitted}


def _replace_uncommitted_error(target_paths, target_dir):
    target_dir_desc = cmd_impl_support.cwd_desc(target_dir)
    cli.out(
        f"guild: files in {target_dir_desc} have uncommitted changes:",
        err=True,
    )
    data = [{"path": path} for path in sorted(target_paths)]
    cli.table(data, ["path"], indent=2, err=True)
    cli.out(
        "Commit these changes or use --replace to skip this check.",
        err=True,
    )
    raise SystemExit()


def _maybe_preview_merge(merge, target_dir, args):
    if args.yes:
        return
    _preview_merge(merge, target_dir)
    if not cli.confirm("Continue (y/N)?", False):
        raise SystemExit(exit_code.ABORTED)


def _preview_merge(merge, target_dir):
    target_dir_desc = cmd_impl_support.cwd_desc(target_dir)
    cli.out(f"You are about to copy files from the following run to {target_dir_desc}:")
    _preview_merge_run(merge)
    _preview_merge_files(merge)


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


def _preview_merge_files(merge):
    cli.out("Files to copy:", err=True)
    data = _format_merge_files(_sorted_merge_files(merge))
    cols = [
        "target_path",
    ]
    cli.table(data, cols, indent=2, err=True)


def _sorted_merge_files(merge):
    return sorted(merge.files, key=lambda mf: mf.target_path)


def _format_merge_files(merge_files):
    return [
        {
            "run_path": f.run_path,
            "target_path": f.target_path,
        }
        for f in merge_files
    ]


def _on_merge_copy(_merge, merge_file, _src, _dest):
    log.info(f"Copying {merge_file.target_path}")
