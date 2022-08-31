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

from guild import batch_util
from guild import cli
from guild import config
from guild import publish as publishlib
from guild import util

from . import runs_impl


def publish(args, ctx=None):
    if args.files and args.all_files:
        cli.error("--files and --all-files cannot both be used")
    if args.refresh_index:
        _refresh_index(args)
    else:
        _publish(args, ctx)
    _report_dir_size(args)


def _publish(args, ctx):
    dest = args.dest or publishlib.DEFAULT_DEST_HOME
    preview = f"You are about to publish the following run(s) to {dest}:"
    confirm = "Continue?"
    no_runs = "No runs to publish."

    def publish_f(runs, formatted):
        _publish_runs(runs, formatted, args)
        _refresh_index(args, no_dest=True)

    def select_runs_f(args, ctx, default_runs_arg):
        runs = runs_impl.runs_op_selected(args, ctx, default_runs_arg)
        return [
            run for run in runs if args.include_batch or not batch_util.is_batch(run)
        ]

    runs_impl.runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs,
        publish_f,
        runs_impl.ALL_RUNS_ARG,
        True,
        select_runs_f,
    )


def _publish_runs(runs, formatted, args):
    if args.all_files:
        copy_files = publishlib.COPY_ALL_FILES
    elif args.files or args.include_links:
        copy_files = publishlib.COPY_DEFAULT_FILES
    else:
        copy_files = None
    for run, frun in zip(runs, formatted):
        cli.out(f"Publishing [{frun['short_id']}] {frun['operation']}... ", nl=False)
        frun["_run"] = run
        try:
            publishlib.publish_run(
                run,
                dest=args.dest,
                template=args.template,
                copy_files=copy_files,
                include_links=args.include_links,
                md5s=not args.no_md5,
                formatted_run=frun,
            )
        except publishlib.PublishError as e:
            cli.error(f"error publishing run {run.id}:\n{e}")
        else:
            dest = args.dest or publishlib.DEFAULT_DEST_HOME
            size = util.dir_size(os.path.join(dest, run.id))
            cli.out(f"using {util.format_bytes(size)}")


def _refresh_index(args, no_dest=False):
    if no_dest:
        dest_suffix = ""
    else:
        dest_suffix = f" in {args.dest or publishlib.DEFAULT_DEST_HOME}"
    print(f"Refreshing runs index{dest_suffix}")
    index_template = _index_template(args)
    try:
        publishlib.refresh_index(args.dest, index_template)
    except publishlib.TemplateError as e:
        cli.error(f"error refreshing index: {e}")


def _index_template(args):
    if not args.index_template:
        return None
    index_template = os.path.join(config.cwd(), args.index_template)
    if not os.path.exists(index_template):
        cli.error(f"index template '{index_template}' does not exist")
    if os.path.isdir(index_template):
        return _index_template_readme(index_template)
    return index_template


def _index_template_readme(dir):
    assert os.path.isdir(dir), dir
    path = os.path.join(dir, "README.md")
    if not os.path.exists(path):
        cli.error(f"index template '{dir}' is missing README.md")
    return path


def _report_dir_size(args):
    dest = args.dest or publishlib.DEFAULT_DEST_HOME
    size = util.dir_size(dest)
    cli.out(f"Published runs using {util.format_bytes(size)}")
