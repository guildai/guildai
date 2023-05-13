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
import sys

from guild import index as indexlib
from guild import run as runlib
from guild import run_manifest
from guild import run_util
from guild import serving_util
from guild import timerange
from guild import util
from guild import var

from . import runs_impl

DEFAULT_RUN_FILE_MAX_SIZE = 10**6


def json_resp(f0):
    def f(*args, **kw):
        try:
            return serving_util.json_resp(f0(*args, **kw))
        except serving_util.HTTPException as e:
            return serving_util.json_resp({"error": e.code, "msg": str(e)}, e.code)

    return f


def main(args):
    if args.get:
        _get_and_exit(args)
    host, port = _host_and_port(args)
    view_url = util.local_server_url(host, port)
    sys.stdout.write(f"Running Guild API server at {view_url} (Type Ctrl-C to quit)\n")
    _serve(host, port)
    sys.stdout.write("\n")


def _get_and_exit(args):
    resp = serving_util.request_get(_api_app(), args.get)
    exit = 0 if resp["status"] == "200 OK" else 1
    for part in resp["body"]:
        sys.stdout.write(part.decode())
    sys.exit(exit)


def _host_and_port(args):
    return (
        args.host or "0.0.0.0",
        args.port or util.free_port(),
    )


def _serve(host, port):
    app = _api_app()
    server = serving_util.make_server(host, port, app)
    server.serve_forever()


def _api_app(cache_ttl=5, cache_prune_threshold=1000):
    cache = util.Cache(cache_ttl, prune_threshold=cache_prune_threshold)
    routes = serving_util.Map(
        [
            ("/runs/", _handle_runs, (cache,)),
            ("/runs/<run_id>/attrs/<attr_name>", _handle_run_attr, (cache,)),
            ("/runs/<run_id>/attrs", _handle_run_multi_attr, (cache,)),
            ("/runs/<run_id>/scalars", _handle_run_scalars, (cache,)),
            ("/runs/<run_id>/files/", _handle_run_files, (cache,)),
            ("/runs/<run_id>/files/<path:path>", _handle_run_file, (cache,)),
            ("/runs/<run_id>/comments", _handle_run_comments, (cache,)),
            ("/runs/<run_id>/tags", _handle_run_tags, (cache,)),
            ("/operations/", _handle_operations, (cache,)),
            ("/cache", _handle_cache, (cache,)),
            ("/<path:path>", _handle_not_supported, ()),
        ]
    )
    return serving_util.App(routes)


@json_resp
def _handle_not_supported(_req, path):
    raise serving_util.NotFound(path)


@json_resp
def _handle_runs(req, cache):
    return cache.read(_cache_key_for_req(req), (_read_runs, (req.args,)))


def _cache_key_for_req(req):
    if not req.args:
        return req.url
    return "?".join([req.url, _cache_key_part_for_args(req.args)])


def _cache_key_part_for_args(args):
    kv = []
    for key in sorted(args.keys()):
        for val in sorted(args.getlist(key)):
            kv.append(f"{key}={val}")
    return "&".join(kv)


def _read_runs(args):
    return [
        {
            "id": run.id,
            "operation": run_util.format_operation(run, nowarn=True),
            "started": run.get("started"),
            "stopped": run.get("stopped"),
            "label": run.get("label"),
            "status": run.status,
        } for run in var.runs(filter=_runs_filter(args))
    ]


def _runs_filter(args):
    filters = []
    _apply_status_filter(args, filters)
    _apply_operation_filter(args, filters)
    _apply_started_filter(args, filters)
    return var.run_filter("all", filters) if filters else None


def _apply_status_filter(args, filters):
    status_list = args.getlist("status")
    if status_list:
        filters.append(
            var.run_filter(
                "any",
                [var.run_filter("attr", "status", status) for status in status_list],
            )
        )


def _apply_operation_filter(args, filters):
    op_list = args.getlist("op")
    if op_list:
        filters.append(runs_impl.operation_filter(op_list))


def _apply_started_filter(args, filters):
    started = args.get("started")
    if started:
        start, end = _parse_timerange(started)
        filters.append(runs_impl.started_filter(start, end))


def _parse_timerange(spec):
    try:
        return timerange.parse_spec(spec)
    except ValueError as e:
        raise serving_util.BadRequest(*e.args)


@json_resp
def _handle_run_attr(req, cache, run_id, attr_name):
    return cache.read(
        _cache_key_for_req(req),
        (_read_run_attr, (run_id, attr_name)),
    )


def _read_run_attr(run_id, attr_name):
    return _run_for_id(run_id).get(attr_name)


def _run_for_id(run_id):
    run_dir = os.path.join(var.runs_dir(), run_id)
    if not os.path.isdir(run_dir):
        raise serving_util.NotFound()
    return runlib.for_dir(run_dir)


@json_resp
def _handle_run_multi_attr(req, cache, run_id):
    return {
        attr_name: cache.read(
            _cache_key_for_req(req),
            (_read_run_attr, (run_id, attr_name)),
        )
        for attr_name in req.args.keys()
    }


@json_resp
def _handle_run_scalars(req, cache, run_id):
    return cache.read(
        _cache_key_for_req(req),
        (_read_run_scalars, (run_id,)),
    )


def _read_run_scalars(run_id):
    run = _run_for_id(run_id)
    index = indexlib.RunIndex()
    index.refresh([run], ["scalar"])
    return [util.dict_to_camel_case(s) for s in index.run_scalars(run)]


def _handle_cache(_req, cache):
    return serving_util.json_resp(sorted(cache.entries()))


@json_resp
def _handle_run_files(req, cache, run_id):
    return cache.read(
        _cache_key_for_req(req),
        (_read_run_files, (run_id,)),
    )


def _read_run_files(run_id):
    run = _run_for_id(run_id)
    manifest_index = _run_manifest_index(run)
    files = _run_files_for_dir(run.dir, "", manifest_index)
    return files


def _run_manifest_index(run):
    try:
        m = run_manifest.manifest_for_run(run.dir)
    except FileNotFoundError:
        return {}
    else:
        with m:
            return {args[1]: args for args in m}


def _run_manifest_index(run):
    return {
        path: entry[0] if entry else None
        for path, entry in run_manifest.iter_run_files(run.dir)
    }


def _run_files_for_dir(path, relpath, manifest_index):
    files = []
    _apply_files(path, relpath, manifest_index, files)
    return files


def _apply_files(path, relpath, manifest_index, files):
    for entry in os.scandir(path):
        stat = entry.stat()
        entry_relpath = os.path.join(relpath, entry.name)
        files.append(
            {
                "name": entry.name,
                "isFile": entry.is_file(),
                "isDir": entry.is_dir(),
                "isLink": entry.is_symlink(),
                "isText": util.is_text_file(os.path.join(path, entry.name)),
                "size": stat.st_size,
                "mtime": int(stat.st_mtime * 1000),
                **_dir_attrs(entry, entry_relpath, manifest_index),
                **_manifest_attrs(entry, entry_relpath, manifest_index),
            }
        )


def _dir_attrs(entry, relpath, manifest_index):
    if not entry.is_dir():
        return {}
    return {
        "files": _run_files_for_dir(entry.path, relpath, manifest_index),
    }


def _manifest_attrs(entry, relpath, manifest_index):
    args = manifest_index.get(relpath)
    return {
        "mType": _manifest_type(args, entry, relpath),
    }


def _manifest_type(args, entry, relpath):
    return args[0] if args else _maybe_generated(entry, relpath)


def _maybe_generated(entry, relpath):
    """Returns 'g' if entry/relpath is generated.

    Generated is an inferred manifest type - it's not written to the
    manifest. We conclude that something is generated if a) it's not a
    directory and b) it's not an internal Guild file (i.e. is not
    located under `.guild/` in the run.

    This is the same logic implemented by `guild ls` when filtering
    generated files.
    """
    return "g" if not entry.is_dir() and not _is_guild_path(relpath) else None


@json_resp
def _handle_run_file(req, cache, run_id, path):
    run = _run_for_id(run_id)
    size, contents = _read_run_file(run, path, _max_size_arg(req))
    return {
        "run": run_id,
        "path": path,
        "size": size,
        "contents": contents,
    }


def _max_size_arg(req):
    val = req.args.get("maxsize")
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _read_run_file(run, path, max_size=None):
    max_size = max_size or DEFAULT_RUN_FILE_MAX_SIZE
    full_path = os.path.join(run.dir, path)

    try:
        stat = os.stat(full_path)
    except FileNotFoundError:
        raise serving_util.NotFound(f"{run.id}/{path}")
    else:
        with open(os.path.join(run.dir, path)) as f:
            return stat.st_size, f.read(max_size)


def _is_guild_path(path):
    return path.split(os.path.sep, 1)[0] == ".guild"


@json_resp
def _handle_run_comments(req, cache, run_id):
    return cache.read(
        _cache_key_for_req(req),
        (_read_comments, (run_id,)),
    )


def _read_comments(run_id):
    run = _run_for_id(run_id)
    return run.get("comments") or []


@json_resp
def _handle_run_tags(req, cache, run_id):
    return cache.read(_cache_key_for_req(req), (_read_tags, (run_id,)))


def _read_tags(run_id):
    run = _run_for_id(run_id)
    return run.get("tags") or []


@json_resp
def _handle_operations(req, cache):
    return cache.read(_cache_key_for_req(req), _read_operations)


def _read_operations():
    return sorted({run_util.format_operation(run, nowarn=True) for run in var.runs()})
