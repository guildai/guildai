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

from guild import cli
from guild import cmd_impl_support
from guild import exit_code
from guild import run_merge
from guild import run_util
from guild import util

from . import runs_impl


def main(args, ctx):
    run = runs_impl.one_run(args, ctx)
    merge = _init_run_merge(run, args)
    target_dir = args.target_dir or _checked_cwd(run, ctx)
    if not args.yes:
        _preview_merge(merge, target_dir)
        if not cli.confirm("Continue (y/N)?", False):
            raise SystemExit(exit_code.ABORTED)
    run_merge.apply_run_merge(merge, target_dir)


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
    check by specifying --target-dir in the command.
    """
    _checked_cwd_run_pkg_type(run, ctx)
    project_dir = _run_project_dir(run)
    cwd = os.getcwd()
    _checked_cwd_matches_project_dir(cwd, project_dir, run, ctx)
    return cwd


def _checked_cwd_run_pkg_type(run, ctx):
    if run.opref.pkg_type not in ("guildfile", "script"):
        cli.error(
            f"run {run.id} does not originate from a project - cannot merge to the "
            "current directory by default\nSpecify --target-dir to skip this "
            f"check or try '{ctx.command_path} --help' for more information."
        )


def _run_project_dir(run):
    project_dir = run_util.run_project_dir(run)
    if not project_dir:
        cli.error(
            f"unexpected missing project directory for run {run.id} ({run.opref})\n"
            "This may be a bug in Guild - please report to "
            "https://github.com/guildai/guildai/issues\n"
            "Skip this check by specifying --target-dir"
        )
    return project_dir


def _checked_cwd_matches_project_dir(cwd, project_dir, run, ctx):
    if not util.compare_paths(cwd, project_dir):
        fmt_project_dir = util.format_dir(project_dir)
        cli.error(
            f"run {run.id} originates from a different directory ({fmt_project_dir}) - "
            "cannot merge to the current directory by default\nSpecify --target-dir "
            f"to override this check or try '{ctx.command_path} --help' for more "
            "information."
        )


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
        for f in sorted(merge_files, key=lambda f: f.run_path)
    ]
