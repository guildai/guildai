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
from guild import run_util
from guild import serving_util
from guild import util
from guild import var


def json_resp(f0):
    def f(*args, **kw):
        try:
            return serving_util.json_resp(f0(*args, **kw))
        except serving_util.NotFound:
            return serving_util.json_resp({"error": 404, "msg": "Not Found"}, 404)

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
            ("/cache", _handle_cache, (cache,)),
        ]
    )
    return serving_util.App(routes)


@json_resp
def _handle_runs(_req, cache):
    return cache.read("/runs", _read_runs)


def _read_runs():
    return [
        {
            "id": run.id,
            "operation": run_util.format_operation(run, nowarn=True),
            "started": run.get("started"),
            "stopped": run.get("stopped"),
            "label": run.get("label"),
            "status": run.status,
        } for run in var.runs()
    ]


@json_resp
def _handle_run_attr(_req, cache, run_id, attr_name):
    return cache.read(
        f"/runs/{run_id}/attrs/{attr_name}",  #
        lambda: _read_run_attr(run_id, attr_name)
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
            f"/runs/{run_id}/attrs/{attr_name}",
            (_read_run_attr, (run_id, attr_name)))
        )
        for attr_name in _attr_names_for_req(req)
    }


def _attr_names_for_req(req):
    return req.args.keys()


@json_resp
def _handle_run_scalars(_req, cache, run_id):
    return cache.read(f"/runs/{run_id}/scalars", lambda: _read_run_scalars(run_id))


def _read_run_scalars(run_id):
    run = _run_for_id(run_id)
    index = indexlib.RunIndex()
    index.refresh([run], ["scalar"])
    return [util.dict_to_camel_case(s) for s in index.run_scalars(run)]


def _handle_cache(_req, cache):
    return serving_util.json_resp(sorted(cache.entries()))
