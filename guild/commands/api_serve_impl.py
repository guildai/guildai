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

import json
import logging
import mimetypes
import os
import sys

from guild import config as configlib
from guild import filter as filterlib
from guild import filter_util
from guild import index as indexlib
from guild import run as runlib
from guild import run_manifest
from guild import run_util
from guild import serving_util
from guild import tfevent
from guild import timerange
from guild import util
from guild import var

from . import runs_impl

log = logging.getLogger("guild")

DEFAULT_RUN_FILE_MAX_SIZE = 10**6


class MethodNotSupported(serving_util.HTTPException):
    code = 400
    description = "method not supported"


def json_resp(f0):
    def f(*args, **kw):
        try:
            resp = f0(*args, **kw)
        except serving_util.HTTPException as e:
            return _json_resp(
                {
                    "error": e.code,
                    "msg": str(e)
                },
                e.code,
            )
        else:
            return _json_resp(resp)

    return f


def _json_resp(resp, code=200):
    return serving_util.json_resp(resp, code, [("Access-Control-Allow-Origin", "*")])


def main(args):
    if args.get:
        _get_and_exit(args)
    if args.post:
        _post_and_exit(args)
    host, port = _host_and_port(args)
    view_url = util.local_server_url(host, port)
    sys.stdout.write(f"Running Guild API server at {view_url} (Type Ctrl-C to quit)\n")
    _serve(host, port)
    sys.stdout.write("\n")


def _get_and_exit(args):
    resp = serving_util.request_get(ApiApp(), args.get)
    exit = 0 if resp["status"] == "200 OK" else 1
    for part in resp["body"]:
        sys.stdout.buffer.write(part)
    sys.exit(exit)


def _post_and_exit(args):
    url, body = args.post
    resp = serving_util.request_post(ApiApp(), url, body)
    exit = 0 if resp["status"] == "200 OK" else 1
    for part in resp["body"]:
        sys.stdout.buffer.write(part)
    sys.exit(exit)


def _host_and_port(args):
    return (
        args.host or "0.0.0.0",
        args.port or util.free_port(),
    )


def _serve(host, port):
    app = ApiApp()
    server = serving_util.make_server(host, port, app)
    server.serve_forever()


def ApiApp():
    routes = serving_util.Map(
        [
            ("/runs/", _handle_runs, ()),
            ("/runs/<run_id>", _handle_run, ()),
            ("/runs/<run_id>/attrs/<attr_name>", _handle_run_attr, ()),
            ("/runs/<run_id>/attrs", _handle_run_multi_attr, ()),
            ("/runs/<run_id>/scalars", _handle_run_scalars, ()),
            ("/runs/<run_id>/files/", _handle_run_files, ()),
            ("/runs/<run_id>/files/<path:path>", _handle_run_file, ()),
            ("/runs/<run_id>/comments", _handle_run_comments, ()),
            ("/runs/<run_id>/tags", _handle_run_tags, ()),
            ("/runs/<run_id>/label", _handle_run_label, ()),
            ("/runs/<run_id>/process-info", _handle_process_info, ()),
            ("/operations", _handle_operations, ()),
            ("/compare", _handle_compare, ()),
            ("/scalars", _handle_scalars, ()),
            ("/collections", _handle_collections, ()),
            ("/ping", _handle_ping, ()),
            ("/<path:path>", _handle_not_supported, ()),
        ]
    )
    return serving_util.App(routes, _error_handler)


def _error_handler(_e):
    def app(env, start_resp):
        log.exception("unhandled error for %s", env)
        resp = _json_resp(
            {
                "error": 500,
                "msg": "Internal Error"
            },
            500,
        )
        return resp(env, start_resp)

    return app


@json_resp
def _handle_not_supported(req, path):
    raise serving_util.NotFound(path)


@json_resp
def _handle_ping(req):
    if req.method != "GET":
        raise MethodNotSupported()
    return True


@json_resp
def _handle_runs(req):
    if req.method == "GET":
        return _read_runs(req.args)
    if req.method == "POST":
        return _exec_runs_op(req)
    raise MethodNotSupported()


def _read_runs(args):
    return [_run_base_attrs(run) for run in _runs_for_args(args)]


def _runs_for_args(args):
    return filter_util.filtered_runs(
        _maybe_parsed_text_filter(args),
        root=_runs_dir(args),
        base_filter=_runs_base_filter(args),
        base_runs=_runs_for_collection(args),
    )


def _runs_dir(args):
    return var.runs_dir(deleted="deleted" in args)


def _runs_for_collection(args):
    collection_name = args.get("collection")
    if not collection_name:
        return None
    collection = _collection_for_name(collection_name)
    if not collection:
        raise serving_util.BadRequest(f"no such collection: {collection_name}")
    return _runs_for_args(_CollectionArgsProxy(collection, args))


def _collection_for_name(name):
    config = configlib.user_config()
    ids = name.split("/")
    return _find_collection(ids, config.get("collections"))


def _find_collection(ids, collections):
    if not collections:
        return None
    cur_id = ids[0]
    for c in collections:
        if c.get("id") == cur_id:
            if len(ids) == 1:
                return c
            return _find_collection(ids[1:], c.get("collections"))
    return None


class _CollectionArgsProxy:
    _proxied_args = (
        "deleted",
        "started",
        "status",
        "op",
        "text",
        "collection",
        "run",
    )

    def __init__(self, collection, args):
        self.c = dict(collection)
        self._apply_deleted(args)

    def _apply_deleted(self, args):
        # Apply 'deleted' from args as this determined where we apply
        # the collection filter
        if "deleted" in args:
            self.c["deleted"] = args.get("deleted")
        else:
            # Ensure invalid config doesn't leak in args
            self.c.pop("deleted", None)

    def get(self, name):
        val = self._get(name)
        if isinstance(val, list):
            return val[0]
        return val

    def _get(self, name):
        assert name in self._proxied_args, name
        if name == "collection":
            # Implementation explicitly prohibits recursive
            # application of collections. While this is conceivable
            # feature, we would need to check for cycles. In this
            # case, the value is always None.
            return None
        val = self.c.get(self._map_arg_name(name))
        return self._ensure_filter_text_prefix(val, name)

    @staticmethod
    def _map_arg_name(name):
        if name == "text":
            return "filter"
        return name

    @staticmethod
    def _ensure_filter_text_prefix(val, name):
        if val is not None and name == "text":
            return f"/{val}"
        return val

    def getlist(self, name):
        val = self._get(name)
        if val is None:
            return []
        if isinstance(val, list):
            return val
        return [val]

    def __iter__(self):
        return (name for name in self._proxied_args if self._get(name) is not None)


def _maybe_parsed_text_filter(args):
    text = (args.get("text") or "").strip()
    if not text:
        return None
    parser = filterlib.parser()
    filter_expr = _maybe_filter_expr(text) or _generic_text_filter_expr(text)
    try:
        return parser.parse(filter_expr)
    except SyntaxError as e:
        raise serving_util.BadRequest(*e.args)


def _maybe_filter_expr(text):
    return text[1:] if text[:1] == "/" else None


def _generic_text_filter_expr(text):
    return (
        f"op contains '{text}' "
        f"or label contains '{text}' "
        f"or tags contains '{text}' "
        f"or id contains '{text}'"
    )


def _runs_base_filter(args):
    filters = []
    _apply_id_filter(args, filters)
    _apply_status_filter(args, filters)
    _apply_operation_filter(args, filters)
    _apply_started_filter(args, filters)
    return var.run_filter("all", filters) if filters else None


def _apply_id_filter(args, filters):
    ids = set(args.getlist("run"))
    if ids:
        filters.append(lambda run: run.id in ids)


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


def _run_base_attrs(run):
    return {
        "id": run.id,
        "dir": run.dir,
        "operation": run_util.format_operation(run, nowarn=True),
        "started": run.get("started"),
        "stopped": run.get("stopped"),
        "label": run.get("label"),
        "status": run.status,
        "deleted": _run_deleted(run),
    }


def _run_deleted(run):
    return "/trash/runs/" in run.dir.replace("\\", "/")


def _exec_runs_op(req):
    op, run_ids = _decode_runs_op(req)
    runs, missing, running = _runs_for_op(op, run_ids)
    if op == "delete":
        var.delete_runs(runs)
    elif op == "restore":
        var.restore_runs(runs)
    elif op == "purge":
        var.purge_runs(runs)
    else:
        assert False, op
    return {
        "applied": [run.id for run in runs],
        "missing": missing,
        "running": running,
    }


def _decode_runs_op(req):
    op = _decode_data(req)
    if not isinstance(op, dict):
        raise serving_util.BadRequest("value must be a dict")
    name = _validate_op_name(op)
    run_ids = _validate_op_run_ids(op)
    return name, run_ids


def _validate_op_name(op):
    name = op.get("name")
    if not name:
        raise serving_util.BadRequest("op name not specified")
    if name not in ("delete", "restore", "purge"):
        raise serving_util.BadRequest("invalid op name")
    return name


def _validate_op_run_ids(op):
    run_ids = op.get("runIds")
    if run_ids is None:
        raise serving_util.BadRequest("runIds not specified")
    if not isinstance(run_ids, list):
        raise serving_util.BadRequest("op runIds must be a list")
    if any(not isinstance(id, str) for id in run_ids):
        raise serving_util.BadRequest("invalid runIds - values must be strings")
    return run_ids


def _runs_for_op(op, run_ids):
    runs = []
    missing = []
    running = []
    runs_dir = var.runs_dir(deleted=op in ("restore", "purge"))
    for run_id in run_ids:
        run = _try_run_for_dir(os.path.join(runs_dir, run_id))
        if not run:
            missing.append(run_id)
        elif run.status == "running":
            running.append(run_id)
        else:
            runs.append(run)
    return runs, missing, running


def _try_run_for_dir(path):
    if os.path.isdir(path):
        return runlib.for_dir(path)
    return None


@json_resp
def _handle_run(req, run_id):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_run(run_id)


def _read_run(run_id):
    return _run_base_attrs(_run_for_id(run_id))


@json_resp
def _handle_run_attr(req, run_id, attr_name):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_run_attr(run_id, attr_name)


def _read_run_attr(run_id, attr_name):
    return _run_for_id(run_id).get(attr_name)


def _run_for_id(run_id):
    for runs_dir in (var.runs_dir(), var.runs_dir(deleted=True)):
        run_dir = os.path.join(runs_dir, run_id)
        if os.path.isdir(run_dir):
            return runlib.for_dir(run_dir)
    raise serving_util.NotFound()


@json_resp
def _handle_run_multi_attr(req, run_id):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_multi_attr(run_id, req.args)


def _read_multi_attr(run_id, args):
    return {attr_name: _read_run_attr(run_id, attr_name) for attr_name in args.keys()}


@json_resp
def _handle_run_scalars(req, run_id):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_run_scalars(run_id)


def _read_run_scalars(run_id, index=None):
    run = _run_for_id(run_id)
    if not index:
        index = indexlib.RunIndex()
        index.refresh([run], ["scalar"])
    return {s["tag"]: _run_scalar_val(s) for s in index.run_scalars(run)}


def _run_scalar_val(scalar):
    val = util.dict_to_camel_case(scalar)
    del val["tag"]
    del val["run"]
    return val


@json_resp
def _handle_compare(req):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_compare_data(req.args)


def _read_compare_data(args):
    runs = var.runs(filter=_runs_base_filter(args))
    index = indexlib.RunIndex()
    index.refresh(runs, ["scalar"])
    return {
        run.id: {
            "flags": run.get("flags"),
            "scalars": _read_run_scalars(run.id, index)
        }
        for run in runs
    }


@json_resp
def _handle_scalars(req):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_scalars_data(req.args)


def _read_scalars_data(args):
    return {
        run.id: _scalars_data_for_run(run)
        for run in var.runs(filter=_runs_base_filter(args))
    }


def _scalars_data_for_run(run):
    return {
        _run_scalars_path(path, run): _scalars_data_for_reader(reader)
        for path, _digest, reader in tfevent.scalar_readers(run.dir)
    }


def _run_scalars_path(reader_path, run):
    return os.path.relpath(reader_path, run.dir)


def _scalars_data_for_reader(reader):
    return [[tag, value, step] for tag, value, step in reader]


@json_resp
def _handle_collections(req):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_collections()


def _read_collections():
    collections = configlib.user_config().get("collections") or []
    _apply_path_ids(collections)
    return collections


def _apply_path_ids(collections, parents=None):
    parents = parents or []
    for c in collections:
        c["id_path"] = _id_path(c, parents)
        _apply_path_ids(c.get("collections") or [], parents + [c])


def _id_path(collection, parents):
    return "/".join([c.get("id", "") for c in parents] + [collection.get("id", "")])


@json_resp
def _handle_run_files(req, run_id):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_run_files(run_id)


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
        stat = _stat_for_entry(entry)
        entry_relpath = os.path.join(relpath, entry.name)
        files.append(
            {
                "name": entry.name,
                "path": entry_relpath,
                "isFile": entry.is_file(),
                "isDir": entry.is_dir(),
                "isLink": entry.is_symlink(),
                "isText": entry.is_file() and util.is_text_file(entry.path),
                "size": stat.st_size if stat else None,
                "mtime": int(stat.st_mtime * 1000) if stat else None,
                **_type_attrs(entry.name),
                **_dir_attrs(entry, entry_relpath, manifest_index),
                **_manifest_attrs(entry, entry_relpath, manifest_index),
            }
        )


def _stat_for_entry(entry):
    try:
        return entry.stat()
    except FileNotFoundError:
        # Occurs for broken symlinks
        return None


def _type_attrs(name):
    type, encoding = mimetypes.guess_type(name)
    return {
        "type": type,
        "encoding": encoding,
    }


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


def _handle_run_file(_req, run_id, path):
    run = _run_for_id(run_id)
    full_path = os.path.join(run.dir, path)

    def not_found(env, start_resp):
        app = _json_resp({"error": 404, "msg": "Not Found"}, 404)
        return app(env, start_resp)

    static_app = serving_util.SharedDataMiddleware(not_found, {full_path: full_path})

    def app(env, start_resp):
        env["PATH_INFO"] = full_path

        def start_resp_allow_origin(status, headers):
            headers.extend(
                [
                    ("Access-Control-Allow-Origin", "*"),
                    ("Cache-Control", "no-cache"),
                ]
            )
            _maybe_plain_text_type(full_path, headers)
            start_resp(status, headers)

        return static_app(env, start_resp_allow_origin)

    return app


def _maybe_plain_text_type(path, headers):
    content_type_h = util.pop_find(headers, lambda h: h[0].lower() == 'content-type')
    if not content_type_h:
        return
    headers.append(
        ('Content-Type', 'text/plain')  #
        if _force_plain_text(path, content_type_h[1])  #
        else content_type_h
    )


def _force_plain_text(path, content_type):
    return content_type == 'application/octet-stream' and util.is_text_file(path)


def _is_guild_path(path):
    return path.split(os.path.sep, 1)[0] == ".guild"


@json_resp
def _handle_run_comments(req, run_id):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_comments(run_id)


def _read_comments(run_id):
    run = _run_for_id(run_id)
    return run.get("comments") or []


@json_resp
def _handle_run_tags(req, run_id):
    if req.method == "GET":
        return _read_tags(run_id)
    if req.method == "POST":
        return _set_run_tags(req, run_id)
    raise MethodNotSupported()


def _read_tags(run_id):
    run = _run_for_id(run_id)
    return run.get("tags") or []


def _set_run_tags(req, run_id):
    run = _run_for_id(run_id)
    tags = _decode_tags(req)
    if not tags:
        run.del_attr("tags")
    else:
        run.write_attr("tags", tags)
    return True


def _decode_tags(req):
    l = _decode_data(req)
    if not isinstance(l, list):
        raise serving_util.BadRequest("value must be a list")
    return [str(x).strip() for x in l]


@json_resp
def _handle_run_label(req, run_id):
    if req.method == "GET":
        return _read_run_attr(run_id, "label")
    if req.method == "POST":
        return _set_run_label(req, run_id)
    raise MethodNotSupported()


def _set_run_label(req, run_id):
    run = _run_for_id(run_id)
    label = _decode_data(req)
    if not isinstance(label, str):
        raise serving_util.BadRequest("value must be a string")
    label = label.strip()
    if not label:
        run.del_attr("label")
    else:
        run.write_attr("label", label)
    return True


def _decode_data(req):
    data = req.get_data()
    try:
        return json.loads(data)
    except ValueError:
        raise serving_util.BadRequest("invalid JSON encoding") from None


@json_resp
def _handle_process_info(req, run_id):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_process_info(run_id)


def _read_process_info(run_id):
    run = _run_for_id(run_id)
    return {
        "exitStatus": run.get("exit_status"),
        "command": run.get("cmd"),
        "environment": run.get("env"),
    }


@json_resp
def _handle_operations(req):
    if req.method != "GET":
        raise MethodNotSupported()
    return _read_operations(req.args)


def _read_operations(args):
    return sorted(
        {
            run_util.format_operation(run, nowarn=True)
            for run in var.runs(var.runs_dir(deleted="deleted" in args))
        }
    )
