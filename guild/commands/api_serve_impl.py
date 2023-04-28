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

import sys

from guild import run_util
from guild import serving_util
from guild import util
from guild import var


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


def _api_app(cache_ttl=5):
    cache = util.Cache(cache_ttl)
    routes = serving_util.Map([
        ("/runs", _handle_runs, (cache,)),
    ])
    return serving_util.App(routes)


def _handle_runs(_req, cache):
    runs = cache.read("runs", _gen_runs)
    return serving_util.json_resp(runs)


def _gen_runs():
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
