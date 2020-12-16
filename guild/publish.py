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

import codecs
import collections
import csv
import datetime
import os
import re
import shutil
import stat

import jinja2
import six
import yaml

from guild import guildfile
from guild import run_util
from guild import util
from guild import yaml_util

DEFAULT_DEST_HOME = "published-runs"
DEFAULT_TEMPLATE = "default"

COPY_DEFAULT_FILES = 1
COPY_ALL_FILES = 2


class PublishError(Exception):
    pass


class TemplateError(PublishError):
    def __init__(self, e):
        super(TemplateError, self).__init__(e)
        self._e = e

    def __str__(self):
        if hasattr(self._e, "filename"):
            return self._default_str()
        else:
            return super(TemplateError, self).__str__()

    def _default_str(self):
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
        return "%s: %s" % (_format_template_files(self._template), self._e.message)


def _format_template_files(t):
    if len(t.files) == 1:
        basename = t.files[0]
    else:
        basename = "{%s}" % ",".join(sorted(t.files))
    return os.path.join(t.path, basename)


class RunFilters(object):

    IMG_PATTERN = re.compile(r"\.(png|gif|jpe?g|tiff?|bmp|webp)", re.IGNORECASE)

    def __init__(self, run_dest):
        self.run_dest = run_dest

    def install(self, env):
        env.filters.update(
            {
                "csv_dict_rows": self.csv_dict_rows,
                "empty": self.empty,
                "file_size": self.file_size,
                "flag_val": self.flag_val,
                "nbhyph": self.nbhyph,
                "nbsp": self.nbsp,
                "runfile_link": self.runfile_link,
                "scalar_key": self.scalar_key,
                "short_id": self.short_id,
                "utc_date": self.utc_date,
            }
        )

    @staticmethod
    def empty(val):
        if val in (None, "") or isinstance(val, jinja2.Undefined):
            return ""
        return val

    @staticmethod
    def flag_val(val):
        if isinstance(val, jinja2.Undefined):
            return ""
        return run_util.format_attr(val)

    def runfile_link(self, path):
        if self.run_dest is None:
            raise TemplateError(
                "runfile_link cannot be used in this context " "(not publishing a run"
            )
        if not isinstance(path, six.string_types):
            return ""
        maybe_runfile = os.path.join(self.run_dest, "runfiles", path)
        if os.path.isfile(maybe_runfile):
            return "runfiles/" + path
        return None

    @staticmethod
    def utc_date(val, unit="s"):
        if not isinstance(val, (int, float) + six.string_types):
            return ""
        try:
            val = int(val)
        except (ValueError, TypeError):
            return ""
        else:
            if unit == "s":
                ts = val * 1000000
            elif unit == "ms":
                ts = val * 1000
            elif unit == "us":
                ts = val
            else:
                raise ValueError("unsupported unit %r (expected s, ms, or us)" % unit)
            return util.utcformat_timestamp(ts)

    @staticmethod
    def file_size(val):
        if not isinstance(val, (int, float) + six.string_types):
            return ""
        try:
            bytes = int(val)
        except (ValueError, TypeError):
            return ""
        else:
            return util.format_bytes(bytes)

    @staticmethod
    def scalar_key(s):
        return run_util.run_scalar_key(s)

    @staticmethod
    def csv_dict_rows(csv_rows):
        keys = csv_rows[0]
        return [dict(zip(keys, row)) for row in csv_rows[1:]]

    @staticmethod
    def nbsp(x):
        if not x:
            return "&nbsp;"
        return x

    @staticmethod
    def short_id(id):
        if not isinstance(id, six.string_types):
            return ""
        return id[:8]

    @staticmethod
    def nbhyph(s):
        if not s:
            return s
        return s.replace("-", "&#8209;")


class Template(object):
    def __init__(self, path, run_dest=None, filters=None):
        if not os.path.exists(path):
            raise RuntimeError("invalid template source: %s" % path)
        self.path = path
        self._file_templates = sorted(_init_file_templates(path, run_dest, filters))

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


def _init_file_templates(path, run_dest=None, filters=None):
    ts = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if name[:1] == "_":
                continue
            abspath = os.path.join(root, name)
            relpath = os.path.relpath(abspath, path)
            template = _init_file_template(abspath, run_dest, filters)
            ts.append((relpath, abspath, template))
    return ts


def _init_file_template(path, run_dest=None, filters=None):
    """Returns template for path or None if path is not a text file.

    Raises TemplateError if path does not exist or cannot be parsed as
    a template.
    """
    if not os.path.exists(path):
        raise TemplateError("%s does not exist" % path)
    if not util.is_text_file(path):
        return None
    dirname, basename = os.path.split(path)
    templates_home = _local_path("templates")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([dirname, templates_home]),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
    )
    RunFilters(run_dest).install(env)
    if filters:
        env.filters.update(filters)
    try:
        return env.get_template(basename)
    except jinja2.TemplateError as e:
        raise TemplateError(e)


def _render_template(template, vars, dest):
    with open(dest, "w") as f:
        for part in template.generate(vars):
            f.write(part)
        f.write(os.linesep)


PublishRunState = collections.namedtuple(
    "PublishRunState",
    [
        "run",
        "opdef",
        "copy_files",
        "include_links",
        "formatted_run",
        "dest_home",
        "template",
        "run_dest",
        "md5s",
    ],
)


def publish_run(
    run,
    dest=None,
    template=None,
    copy_files=None,
    include_links=False,
    md5s=True,
    formatted_run=None,
):
    state = _init_publish_run_state(
        run, dest, template, copy_files, include_links, md5s, formatted_run
    )
    _init_published_run(state)
    _publish_run_guild_files(state)
    _copy_sourcecode(state)
    _copy_runfiles(state)
    _generate_template(state)


def _init_publish_run_state(
    run, dest, template, copy_files, include_links, md5s, formatted_run
):
    dest_home = dest or DEFAULT_DEST_HOME
    opdef = _run_opdef(run)
    run_dest = _published_run_dest(dest_home, run)
    template = _init_template(template, opdef, run_dest)
    if not formatted_run:
        formatted_run = _format_run_for_publish(run)
    return PublishRunState(
        run,
        opdef,
        copy_files,
        include_links,
        formatted_run,
        dest_home,
        template,
        run_dest,
        md5s,
    )


def _run_opdef(run):
    try:
        gf = guildfile.for_run(run)
    except (guildfile.NoModels, guildfile.GuildfileMissing, TypeError):
        return None
    else:
        assert run.opref, run.path
        try:
            m = gf.models[run.opref.model_name]
        except KeyError:
            return None
        else:
            return m.get_operation(run.opref.op_name)


def _init_template(template, opdef, run_dest):
    template_spec = util.find_apply([lambda: template, lambda: _opdef_template(opdef)])
    template_path = _find_template(template_spec, opdef)
    return Template(template_path, run_dest)


def _opdef_template(opdef):
    return util.find_apply(
        [lambda: _opdef_publish_template(opdef), lambda: DEFAULT_TEMPLATE]
    )


def _opdef_publish_template(opdef):
    if not opdef or not opdef.publish:
        return None
    return opdef.publish.template


def _find_template(name, opdef):
    return util.find_apply(
        [
            lambda: _abs_template(name),
            lambda: _default_template(name),
            lambda: _project_template(name, opdef),
            lambda: _cannot_find_template_error(name),
        ]
    )


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


def _published_run_dest(dest_home, run):
    return os.path.join(dest_home, run.id)


def _format_run_for_publish(run):
    frun = run_util.format_run(run)
    if not frun["stopped"]:
        frun["duration"] = ""
    return frun


def _init_published_run(state):
    """Ensure empty target directory for published run.

    As a side effect, lazily creates `state.dest_home` and creates
    `.guild-nocopy` to ensure that the published runs home is not
    considered by Guild for source snapshots.
    """
    util.ensure_dir(state.dest_home)
    util.touch(os.path.join(state.dest_home, ".guild-nocopy"))
    if os.path.exists(state.run_dest):
        util.safe_rmtree(state.run_dest)
    os.mkdir(state.run_dest)


def _publish_run_guild_files(state):
    _publish_run_info(state)
    _publish_flags(state)
    _publish_scalars(state)
    _publish_output(state)
    _publish_sourcecode_list(state)
    _publish_runfiles_list(state)


def _publish_run_info(state):
    """Write run.yml to run publish dest.

    This function should be kept in sync with output generated by
    `guild runs info` - minus system-specific values (e.g. run_dir and
    pid) and flags (which are written to a separate file).
    """
    run = state.run
    frun = state.formatted_run
    path = os.path.join(state.run_dest, "run.yml")
    encode = lambda x: yaml_util.encode_yaml(x).rstrip()
    fmt_ts = util.utcformat_timestamp
    started = run.get("started")
    stopped = run.get("stopped")
    with codecs.open(path, "w", "utf-8") as f:
        f.write("id: %s\n" % run.id)
        f.write("operation: %s\n" % encode(frun["operation"]))
        f.write("status: %s\n" % encode(frun["status"]))
        f.write("started: %s\n" % fmt_ts(started))
        f.write("stopped: %s\n" % fmt_ts(stopped))
        f.write("time: %s\n" % _format_time(started, stopped))
        f.write("marked: %s\n" % encode(frun["marked"]))
        f.write("label: %s\n" % encode(run.get("label")))
        f.write("command: %s\n" % encode(frun["command"]))
        f.write("exit_status: %s\n" % encode(frun["exit_status"]))


def _format_time(started, stopped):
    if started and stopped:
        return util.format_duration(started, stopped)
    return ""


def _publish_flags(state):
    flags = state.run.get("flags") or {}
    dest = os.path.join(state.run_dest, "flags.yml")
    _save_yaml(flags, dest)


def _save_yaml(val, path):
    with open(path, "w") as f:
        yaml.safe_dump(
            val,
            f,
            default_flow_style=False,
            indent=2,
            encoding="utf-8",
            allow_unicode=True,
        )


def _publish_scalars(state):
    cols = [
        "prefix",
        "tag",
        "count",
        "total",
        "avg_val",
        "first_val",
        "first_step",
        "last_val",
        "last_step",
        "min_val",
        "min_step",
        "max_val",
        "max_step",
    ]
    dest = os.path.join(state.run_dest, "scalars.csv")
    scalars = _run_scalars(state)
    with open(dest, "w") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(cols)
        for s in scalars:
            out.writerow([s[col] for col in cols])


def _run_scalars(state):
    from guild import index as indexlib  # expensive

    index = indexlib.RunIndex()
    index.refresh([state.run], ["scalar"])
    return list(index.run_scalars(state.run))


def _publish_output(state):
    src = state.run.guild_path("output")
    if os.path.isfile(src):
        dest = os.path.join(state.run_dest, "output.txt")
        shutil.copyfile(src, dest)


def _publish_sourcecode_list(state):
    src = state.run.guild_path("sourcecode")
    dest = os.path.join(state.run_dest, "sourcecode.csv")
    paths = _dir_paths(src, skip_guildfiles=True)
    with open(dest, "w") as f:
        _write_paths_csv(paths, src, state.md5s, f)


def _dir_paths(dir, skip_guildfiles=False):
    seen = set()
    paths = []
    for root, dirs, names in os.walk(dir, followlinks=True):
        if skip_guildfiles:
            _remove_guild_dir(dirs)
        for name in dirs + names:
            path = os.path.join(root, name)
            abs_path = os.path.abspath(path)
            if abs_path in seen:
                continue
            seen.add(abs_path)
            paths.append(path)
    paths.sort()
    return paths


def _remove_guild_dir(dirs):
    try:
        dirs.remove(".guild")
    except ValueError:
        pass


def _write_paths_csv(paths, root, md5s, f):
    out = csv.writer(f, lineterminator="\n")
    out.writerow(["path", "type", "size", "mtime", "md5"])
    for path in paths:
        out.writerow(_path_row(path, root, md5s))


def _path_row(path, root, md5):
    try:
        st = os.stat(path)
    except OSError:
        st = None
    try:
        lst = os.lstat(path)
    except OSError:
        lst = None
    return [
        os.path.relpath(path, root),
        _path_type(st, lst),
        st.st_size if st else "",
        _path_mtime(st),
        _path_md5(path, st) if md5 else "",
    ]


def _path_type(st, lst):
    parts = []
    if st:
        if stat.S_ISREG(st.st_mode):
            parts.append("file")
        elif stat.S_ISDIR(st.st_mode):
            parts.append("dir")
        else:
            parts.append("other")
    if lst:
        if stat.S_ISLNK(lst.st_mode):
            parts.append("link")
    return " ".join(parts)


def _path_mtime(st):
    if not st:
        return ""
    return int((st.st_mtime + _utc_offset()) * 1000000)


def _utc_offset():
    try:
        return globals()["__utc_offset"]
    except KeyError:
        globals()["__utc_offset"] = offset = int(
            round(
                (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()
            )
        )
        return offset


def _path_md5(path, st):
    if not st or not stat.S_ISREG(st.st_mode):
        return ""
    return util.file_md5(path)


def _publish_runfiles_list(state):
    dest = os.path.join(state.run_dest, "runfiles.csv")
    paths = _dir_paths(state.run.dir, skip_guildfiles=True)
    with open(dest, "w") as f:
        _write_paths_csv(paths, state.run.dir, state.md5s, f)


def _copy_sourcecode(state):
    src = state.run.guild_path("sourcecode")
    if not os.path.isdir(src):
        return
    dest = os.path.join(state.run_dest, "sourcecode")
    shutil.copytree(src, dest)


class PublishRunVars(object):
    def __init__(self, state):
        self._state = state
        self._cache = {}
        self._keys = [
            "flags",
            "output",
            "run",
            "runfiles",
            "scalars",
            "sourcecode",
        ]

    def keys(self):
        return self._keys

    def __getitem__(self, name):
        try:
            return self._cache[name]
        except KeyError:
            self._cache[name] = val = self._load(name)
            return val

    def _load(self, name):
        return util.find_apply([self._load_yaml, self._load_csv, self._load_txt], name)

    def _load_yaml(self, name):
        path = os.path.join(self._state.run_dest, name + ".yml")
        if not os.path.exists(path):
            return None
        return yaml.safe_load(open(path, "r"))

    def _load_csv(self, name):
        path = os.path.join(self._state.run_dest, name + ".csv")
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return list(csv.reader(f))

    def _load_txt(self, name):
        path = os.path.join(self._state.run_dest, name + ".txt")
        if not os.path.exists(path):
            return None
        return open(path, "r").read()


class CopyRunFilesFilter(object):
    def __init__(self, state):
        self._run_dir = state.run.dir
        self._include_links = state.include_links

    def delete_excluded_dirs(self, root, dirs):
        self._delete_guild_dir(dirs)
        self._maybe_delete_links(root, dirs)

    @staticmethod
    def _delete_guild_dir(dirs):
        try:
            dirs.remove(".guild")
        except ValueError:
            pass

    def _maybe_delete_links(self, root, dirs):
        if self._include_links:
            return
        for name in list(dirs):
            if os.path.islink(os.path.join(root, name)):
                dirs.remove(name)

    def default_select_path(self, path):
        if os.path.islink(path):
            return self._include_links
        return True

    @staticmethod
    def pre_copy(_to_copy):
        pass


def _copy_runfiles(state):
    if not state.copy_files:
        return
    util.select_copytree(
        state.run.dir,
        _runfiles_dest(state),
        _copy_runfiles_config(state),
        CopyRunFilesFilter(state),
    )


def _runfiles_dest(state):
    return os.path.join(state.run_dest, "runfiles")


def _copy_runfiles_config(state):
    if state.copy_files == COPY_ALL_FILES or not state.opdef:
        return []
    return [state.opdef.publish.files]


def _generate_template(state):
    template = state.template
    render_vars = PublishRunVars(state)
    try:
        template.generate(state.run_dest, render_vars)
    except jinja2.TemplateRuntimeError as e:
        raise GenerateError(e, template)
    except jinja2.exceptions.TemplateNotFound as e:
        e.message = "template not found: %s" % e.message
        raise GenerateError(e, template)


def _template_config(opdef):
    if not opdef or not opdef.publish:
        return {}
    config = opdef.publish.get("config") or {}
    return {name.replace("-", "_"): val for name, val in config.items()}


def refresh_index(dest, index_template_path=None):
    dest_home = dest or DEFAULT_DEST_HOME
    if not index_template_path:
        index_template_path = _local_path("templates/runs-index/README.md")
    template = _init_file_template(index_template_path)
    index_path = os.path.join(dest_home, "README.md")
    runs = _published_runs(dest_home)
    _render_template(template, {"runs": runs}, index_path)


def _published_runs(dest_home):
    runs = []
    for name in os.listdir(dest_home):
        run_yml = os.path.join(dest_home, name, "run.yml")
        if not os.path.exists(run_yml):
            continue
        info = yaml.safe_load(open(run_yml, "r"))
        runs.append(info)
    return sorted(runs, key=lambda run: run.get("started"), reverse=True)
