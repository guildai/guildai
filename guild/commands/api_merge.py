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

import click

from guild import click_util

from . import api_support
from . import runs_merge


@click.command("merge")
@api_support.output_options
@runs_merge.merge_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def main(ctx, args):
    """Provides merge support.

    Use '--preview' to generate JSON output describing a merge.

    This command does not prompt for user input. If '--yes' is not
    specified, the command fails with an error.
    """
    from guild.util import StderrCapture
    from .merge_impl import main_with_system_exit_detail as merge_main
    from .merge_impl import SystemExitWithDetail

    _check_merge_without_yes(args, ctx)

    with StderrCapture() as out:
        try:
            merge_main(args, ctx)
        except SystemExitWithDetail as e:
            _handle_exit(e.code, e.detail, out.get_value(), args)
        except SystemExit as e:
            # Calling `main_with_system_exit_detail` should not raise
            # SystemExit - any system exit related exception should be
            # wrapped in `SystemExitWithDetail`. See class docs for
            # `guild.commands.merge_impl.SystemExitWithDetail` for
            # more information.
            assert False, e
        else:
            _handle_exit(0, None, out.get_value(), args)


def _check_merge_without_yes(args, ctx):
    from guild import cli

    if not args.preview and not args.yes:
        cli.error(
            "--yes must be specified for this command when --preview is not used\n"
            f"Try '{ctx.command_path} --help' for more information."
        )


def _handle_exit(code, detail, output, args):
    from . import merge_impl

    if detail is None and code == 0:
        _handle_merge_success(output, args)
    elif isinstance(detail, merge_impl.PreviewMergeDetail):
        _handle_preview(detail.merge, args)
    elif isinstance(detail, merge_impl.ReplacementPathsDetail):
        _handle_replacement_paths(detail.paths, args)
    elif isinstance(detail, merge_impl.UnstagedPathsDetail):
        _handle_unstaged_paths(detail.paths, args)
    elif isinstance(detail, merge_impl.NothingToCopyDetail):
        _handle_nothing_to_copy(args)
    else:
        _handle_other_error(code, detail, output, args)


def _handle_merge_success(output, args):
    resp = {
        "resp": "ok",
        "copied": _parse_copied_files(output),
    }
    api_support.out(resp, args)


def _parse_copied_files(output):
    return [_copied_file_for_output(line) for line in output.split('\n') if line]


def _copied_file_for_output(line):
    assert line.startswith("Copying "), line
    return line[8:]


def _handle_preview(merge, args):
    resp = {
        "resp": "preview",
        "run": _run_data(merge.run),
        "targetDir": os.path.abspath(merge.target_dir),
        "toCopy": [_copy_file_data(f) for f in merge.to_copy],
        "toSkip": [_skip_file_data(f) for f in merge.to_skip],
    }
    api_support.out(resp, args)


def _run_data(run):
    from .view_impl import run_data

    attrs = (
        "id",
        "shortId",
        "dir",
        "operation",
        "started",
        "stopped",
        "label",
        "status",
        "projectDir",
        "opRef",
    )
    data = run_data(run)
    return {name: data.get(name) for name in attrs}


def _copy_file_data(f):
    return {
        "fileType": f.file_type,
        "runPath": f.run_path,
        "targetPath": f.target_path,
    }


def _skip_file_data(f):
    return {
        "fileType": f.file_type,
        "runPath": f.run_path,
        "targetPath": f.target_path,
        "reason": f.reason,
    }


def _handle_replacement_paths(paths, args):
    resp = {
        "resp": "replacement-paths",
        "paths": sorted(paths),
    }
    api_support.out(resp, args)


def _handle_nothing_to_copy(args):
    resp = {"resp": "nothing-to-copy"}
    api_support.out(resp, args)


def _handle_unstaged_paths(paths, args):
    resp = {
        "resp": "unstaged-paths",
        "paths": sorted(paths),
    }
    api_support.out(resp, args)


def _handle_other_error(code, detail, output, args):
    resp = {
        "resp": "other-error",
        "code": code,
        "detail": str(detail),
        "output": output,
    }
    api_support.out(resp, args)
