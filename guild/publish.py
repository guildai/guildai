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
import re
import shutil

import jinja2

from guild import guildfile
from guild import index2 as indexlib
from guild import run_util
from guild import util
from guild import var

DEFAULT_DEST_HOME = "published-runs"
DEFAULT_TEMPLATE = "default"

class PublishError(Exception):
    pass

class TemplateError(PublishError):

    def __init__(self, e):
        super(TemplateError, self).__init__(e)
        self._e = e

    def __str__(self):
        e = self._e
        msg = e.filename
        if hasattr(e, "lineno"):
            msg += ":" + str(e.lineno)
        if e.message:
            msg += ": " + e.message
        return msg

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

    IMG_PATTERN = re.compile(
        r"\.(png|gif|jpe?g|tiff?|bmp|webp)",
        re.IGNORECASE)

    @classmethod
    def install(cls, env):
        env.filters.update({
            "env": cls._env,
            "files": cls._files,
            "source": cls._source,
            "images": cls._images,
            "flags": cls._flags,
            "scalars": cls._scalars,
            "scalar_key": cls._scalar_key,
            "op_desc": cls._op_desc,
            "safe_cell": cls._safe_cell,
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

    @classmethod
    def _images(cls, run):
        return _format_run_files(run["_run"], filter=cls.IMG_PATTERN)

    @staticmethod
    def _flags(run):
        run = run["_run"]
        return sorted((run.get("flags") or {}).items())

    @staticmethod
    def _scalars(run):
        run = run["_run"]
        index = indexlib.RunIndex()
        index.refresh([run], ["scalar"])
        return list(index.run_scalars(run))

    @staticmethod
    def _scalar_key(s):
        prefix = s["prefix"]
        if prefix:
            return "%s#%s" % (s["prefix"], s["tag"])
        else:
            return s["tag"]

    @staticmethod
    def _op_desc(run):
        model = run.get("model")
        op = run.get("op_name")
        if model:
            return "%s:%s" % (model, op)
        else:
            return op

    @staticmethod
    def _safe_cell(x):
        if not x:
            return "&nbsp;"
        return x

def _format_run_files(run, subdir=None, filter=None):
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
            if filter and not filter.search(relpath):
                continue
            if os.path.islink(abspath):
                size = "link"
            else:
                size = util.format_bytes(os.path.getsize(abspath))
            mtime = os.path.getmtime(abspath)
            files.append({
                "path": relpath,
                "url": os.path.join(url_relpath, relpath),
                "size": size,
                "modified": util.format_utctimestamp(mtime * 1000000),
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
        if not os.path.exists(path):
            raise RuntimeError("invalid template source: %s" % path)
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
    templates_home = _local_path("templates")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([dirname, templates_home]),
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
        f.write(os.linesep)

def publish_run(run, dest=None, template=None, formatted_run=None):
    opdef = _run_opdef(run)
    dest_home = dest or DEFAULT_DEST_HOME
    template = _init_template(template, opdef)
    run_dest = _published_run_dest(dest_home, run)
    if not formatted_run:
        formatted_run = _format_run_for_publish(run)
    render_vars = {
        "run": formatted_run,
        "config": _template_config(opdef)
    }
    util.ensure_dir(dest_home)
    util.touch(os.path.join(dest_home, ".guild-archive"))
    # Clean target directoy for re-publishing.
    if os.path.exists(run_dest):
        util.safe_rmtree(run_dest)
    # Generate template first, allowing run output to replace template
    # files.
    try:
        template.generate(run_dest, render_vars)
    except jinja2.TemplateRuntimeError as e:
        raise GenerateError(e, template)
    except jinja2.exceptions.TemplateNotFound as e:
        e.message = "template not found: %s" % e.message
        raise GenerateError(e, template)
    else:
        util.copytree(run.path, run_dest)

def _format_run_for_publish(run):
    fmt = run_util.format_run(run)
    # Format adjustments for published run
    if not fmt["stopped"]:
        fmt["duration"] = ""
    return fmt

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

def _published_run_dest(dest_home, run):
    return os.path.join(dest_home, run.id)

def _init_template(template, opdef):
    template_spec = util.find_apply([
        lambda: template,
        lambda: _opdef_template(opdef)
    ])
    template_path = _find_template(template_spec, opdef)
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
    return util.find_apply([
        lambda: _abs_template(name),
        lambda: _default_template(name),
        lambda: _project_template(name, opdef),
        lambda: _cannot_find_template_error(name)])

def _abs_template(name):
    if name[:1] == "." and os.path.exists(name):
        return name
    return None

def _default_template(name):
    if name == "default":
        return _local_path("templates/publish-default")
    return None

def _local_path(path):
    return os.path.join(os.path.dirname(__file__), path)

def _project_template(name, opdef):
    path = os.path.join(opdef.guildfile.dir, name)
    if os.path.exists(path):
        return path
    return None

def _cannot_find_template_error(name):
    raise PublishError("cannot find template %s" % name)

def _template_config(opdef):
    if not opdef or not opdef.publish:
        return {}
    config = opdef.publish.get("config") or {}
    return {
        name.replace("-", "_"): val
        for name, val in config.items()
    }

def refresh_index(dest):
    dest_home = dest or DEFAULT_DEST_HOME
    index_template_path = _local_path("templates/runs-index/README.md")
    index_template = _init_file_template(index_template_path)
    assert index_template, index_template_path
    index_path = os.path.join(dest_home, "README.md")
    runs = _published_runs(dest_home)
    _render_template(index_template, {"runs": runs}, index_path)

def _published_runs(dir):
    runs = var.runs(dir, sort=["-timestamp"])
    return [_format_run_for_publish(run) for run in runs]
