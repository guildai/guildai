# Copyright 2017-2019 TensorHub, Inc.
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

import os
import shutil

import jinja2

from guild import guildfile
from guild import run as runlib
from guild import util

DEFAULT_DEST_HOME = "published-results"
DEFAULT_TEMPLATE = "default"

class PublishError(Exception):
    pass

class TemplateError(PublishError):

    def __init__(self, e):
        super(TemplateError, self).__init__(e)
        self._e = e

    def __str__(self):
        e = self._e
        return "%s:%i: %s" % (e.filename, e.lineno, e.message)

class GenerateError(PublishError):

    def __init__(self, e, template):
        super(GenerateError, self).__init__(e)
        self._e = e
        self._template = template

    def __str__(self):
        return "%s: %s" % (
            _format_template_files(self._template),
            self._e.message)

def _format_template_files(t):
    if len(t.files) == 1:
        basename = t.files[0]
    else:
        basename = "{%s}" % ",".join(sorted(t.files))
    return os.path.join(t.path, basename)

class RunFilters(object):

    @classmethod
    def install(cls, env):
        env.filters.update({
            "env": cls._env,
            "files": cls._files,
            "source": cls._source,
        })

    @staticmethod
    def _env(run):
        env = run["_run"].get("env", {})
        return "\n".join([
            "%s: %s" % (name, val)
            for name, val in sorted(env.items())
        ])

    @staticmethod
    def _files(run):
        return _format_run_files(run["_run"])

    @staticmethod
    def _source(run):
        return _format_run_files(run["_run"], ".guild/source")

def _format_run_files(run, subdir=None):
    files = []
    if subdir:
        source_dir = os.path.join(run.path, subdir)
    else:
        source_dir = run.path
    url_relpath = os.path.relpath(source_dir, run.path)
    for root, dirs, names in os.walk(source_dir):
        _remove_guild_dir(dirs)
        for name in names:
            abspath = os.path.join(root, name)
            relpath = os.path.relpath(abspath, source_dir)
            file_size = os.path.getsize(abspath)
            files.append({
                "path": relpath,
                "url": os.path.join(url_relpath, relpath),
                "size": util.format_bytes(file_size)
            })
    files.sort(key=lambda i: i["path"])
    return files

def _remove_guild_dir(dirs):
    try:
        dirs.remove(".guild")
    except ValueError:
        pass

class Template(object):

    def __init__(self, path):
        self.path = path
        self._file_templates = sorted(_init_file_templates(path))

    @property
    def files(self):
        return [t[0] for t in self._file_templates]

    def generate(self, dest, vars):
        util.ensure_dir(dest)
        for relpath, src, template in self._file_templates:
            file_dest = os.path.join(dest, relpath)
            util.ensure_dir(os.path.dirname(file_dest))
            if template is None:
                shutil.copyfile(src, file_dest)
            else:
                _render_template(template, vars, file_dest)

def _init_file_templates(path):
    ts = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if name[:1] == "_":
                continue
            abspath = os.path.join(root, name)
            relpath = os.path.relpath(abspath, path)
            template = _init_file_template(abspath)
            ts.append((relpath, abspath, template))
    return ts

def _init_file_template(path):
    if not util.is_text_file(path):
        return None
    dirname, basename = os.path.split(path)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([dirname]),
        autoescape=jinja2.select_autoescape(['html', 'xml']))
    RunFilters.install(env)
    try:
        return env.get_template(basename)
    except jinja2.TemplateError as e:
        raise TemplateError(e)

def _render_template(template, vars, dest):
    with open(dest, "w") as f:
        for part in template.generate(vars):
            f.write(part)

def publish_run(run, dest=None, formatted_run=None):
    opdef = _run_opdef(run)
    dest_home = _dest_home(dest, opdef)
    util.ensure_dir(dest_home)
    util.touch(os.path.join(dest_home, ".guild-archive"))
    run_dest = _published_run_dest(dest_home, run)
    template = _init_template(opdef)
    if not formatted_run:
        formatted_run = format_run(run)
    render_vars = {
        "run": formatted_run,
        "config": _template_config(opdef)
    }
    # Clean target directoy for re-publishing.
    if os.path.exists(run_dest):
        util.safe_rmtree(run_dest)
    # Generate template first, allowing run output to replace template
    # files.
    try:
        template.generate(run_dest, render_vars)
    except jinja2.TemplateRuntimeError as e:
        raise GenerateError(e, template)
    else:
        util.copytree(run.path, run_dest)
        # user-friendly (non ID) directory.
        # Write run ID as attr because we are storing the run under a
        _write_run_id(run.id, run_dest)

def _run_opdef(run):
    try:
        gf = guildfile.from_run(run)
    except (guildfile.NoModels, TypeError):
        return None
    else:
        assert run.opref, run.path
        try:
            m = gf.models[run.opref.model_name]
        except KeyError:
            return None
        else:
            return m.get_operation(run.opref.op_name)

def _dest_home(dest_home_arg, opdef):
    return util.find_apply([
        lambda: dest_home_arg,
        lambda: _opdef_publish_dest(opdef),
        lambda: DEFAULT_DEST_HOME])

def _published_run_dest(dest_home, run):
    run_dest_basename = _run_dest_basename(run)
    return os.path.join(dest_home, run_dest_basename)

def _opdef_publish_dest(opdef):
    if not opdef or not opdef.publish:
        return None
    return opdef.publish.get("dest")

def _run_dest_basename(run):
    parts = []
    model = _safe_model_name(run)
    if model:
        parts.append(model)
    parts.append(_safe_op_name(run))
    parts.append(_format_run_started(run))
    parts.append(run.short_id)
    return "-".join(parts)

def _safe_model_name(run):
    return util.safe_filename(run.opref.model_name)

def _safe_op_name(run):
    return util.safe_filename(run.opref.op_name)

def _format_run_started(run):
    started = run.get("started")
    return util.format_timestamp(started, "%Y_%m_%d-%H_%M_%S")

def _init_template(opdef):
    template_name = _opdef_template(opdef)
    template_path = _find_template(template_name, opdef)
    return Template(template_path)

def _opdef_template(opdef):
    return util.find_apply([
        lambda: _opdef_publish_template(opdef),
        lambda: DEFAULT_TEMPLATE
    ])

def _opdef_publish_template(opdef):
    if not opdef or not opdef.publish:
        return None
    return opdef.publish.get("template")

def _find_template(name, opdef):
    if name == "default":
        return _local_path("templates/publish-default")
    elif name[:0] == ".":
        return _project_template(name, opdef)
    else:
        raise PublishError("cannot find template %s" % name)

def _local_path(path):
    return os.path.join(os.path.dirname(__file__), path)

def _project_template(path, opdef):
    return os.path.join(opdef.guildfile.dir, path)

def format_run(run):
    # Function level import as temp measure since the canonical
    # format_run is in commands.runs_impl, which imports this module.
    # Canonical format_run should be moved to guild.run_util or
    # similar.
    from guild.commands import runs_impl
    fmt = runs_impl.format_run(run)
    # Opportunistic use of dict to make run available to filters.
    fmt["_run"] = run
    return fmt

def _template_config(opdef):
    if not opdef or not opdef.publish:
        return {}
    config = opdef.publish.get("config") or {}
    return {
        name.replace("-", "_"): val
        for name, val in config.items()
    }

def _write_run_id(run_id, run_dest_dir):
    run = runlib.Run(run_id, run_dest_dir)
    util.ensure_dir(run.guild_path("attrs"))
    run.write_attr("id", run_id)
