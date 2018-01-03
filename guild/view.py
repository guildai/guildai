# Copyright 2017 TensorHub, Inc.
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
import os
import subprocess
import sys
import threading
import time

import requests

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug import routing
from werkzeug import serving
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware

from guild import util
from guild import var

MODULE_DIR = os.path.dirname(__file__)

class ViewData(object):

    def runs(self, params):
        """Returns a list of runs for request params.

        Params may be a multi-dict of any of the following:

          run         string    Run ID
          op          string    Op filter
          running     boolean   Is running
          completed   boolean   Is completed
          error       boolean   Is error
          terminated  boolean   Is terminated
          all         boolean   Show all runs
          cwd         string    Specify cwd

        If filter is None, returns the default list of runs (e.g. runs
        per command line options).

        """
        raise NotImplementedError()

    def config(self, params):
        """Returns dict of config for request params.

        Refer to `runs` for details on `params`.

        Config dict must contain:

          cwd         string  Cwd used for runs
          titleLabel  string  Label suitable for browser title

        """
        raise NotImplementedError()

class DevServer(threading.Thread):

    def __init__(self, host, port, view_port):
        super(DevServer, self).__init__()
        self.host = host
        self.port = port
        self.view_port = view_port
        self._ready = False

    def run(self):
        args = [
            _devserver_bin(),
            "--progress",
            "--config", _devserver_config(),
        ]
        env = {
            "HOST": self.host,
            "PORT": str(self.port),
            "VIEW_BASE": "http://{}:{}".format(self.host, self.view_port)
        }
        p = subprocess.Popen(args, env=env)
        p.wait()

    def wait_for_ready(self):
        while not self._ready:
            ping_url = (
                "http://{}:{}/assets/favicon.png".format(self.host, self.port)
            )
            try:
                requests.get(ping_url)
            except requests.exceptions.ConnectionError:
                time.sleep(0.1)
            else:
                self._ready = True

def _devserver_bin():
    path = os.path.join(
        MODULE_DIR, "view/node_modules/.bin/webpack-dev-server")
    if not os.path.exists(path):
        raise AssertionError(
            "{} does not exits - did you resolve node dependencies by "
            "running npm install?".format(path))
    return path

def _devserver_config():
    return os.path.join(MODULE_DIR, "view/build/webpack.dev.conf.js")

class StaticBase(object):

    def __init__(self, exports):
        self._app = SharedDataMiddleware(self._not_found, exports)

    def handle(self, _req):
        return self._app

    @staticmethod
    def _not_found(_env, _start_resp):
        raise NotFound()

class DistFiles(StaticBase):

    def __init__(self):
        root = os.path.join(MODULE_DIR, "view/dist")
        super(DistFiles, self).__init__({"/": root})

    def handle_index(self, _req):
        def app(env, start_resp):
            env["PATH_INFO"] = "/index.html"
            return self._app(env, start_resp)
        return app

class RunFiles(StaticBase):

    def __init__(self):
        super(RunFiles, self).__init__({"/runs": var.runs_dir()})

    def handle(self, _req):
        def app(env, start_resp0):
            def start_resp(status, headers):
                headers.append(("Access-Control-Allow-Origin", "*"))
                start_resp0(status, headers)
            return self._app(env, start_resp)
        return app

def serve_forever(data, host, port, no_open=False, dev=False):
    host = host or "localhost"
    if dev:
        _serve_dev(data, host, port, no_open)
    else:
        _serve_prod(data, host, port, no_open)

def _serve_dev(data, host, port, no_open):
    view_port = util.free_port()
    dev_server = DevServer(host, port, view_port)
    dev_server.start()
    dev_server.wait_for_ready()
    if not no_open:
        _open_url(host, port)
    sys.stdout.write(
        " I  Guild View backend: "
        "http://{}:{}\n".format(host, view_port))
    _start_view(data, host, view_port)
    sys.stdout.write("\n")

def _open_url(host, port):
    util.open_url("http://{}:{}".format(host, port))

def _serve_prod(data, host, port, no_open):
    if not no_open:
        _open_url(host, port)
    sys.stdout.write("Running Guild View at http://{}:{}\n".format(host, port))
    _start_view(data, host, port)
    sys.stdout.write("\n")

def _start_view(data, host, port):
    app = _view_app(data)
    server = serving.make_server(host, port, app, threaded=True)
    sys.stdout.flush()
    server.serve_forever()

def _view_app(data):
    dist_files = DistFiles()
    run_files = RunFiles()
    routes = routing.Map([
        routing.Rule("/runs", endpoint=(_handle_runs, (data,))),
        routing.Rule("/runs/<path:_>", endpoint=(run_files.handle, ())),
        routing.Rule("/config", endpoint=(_handle_config, (data,))),
        routing.Rule("/", endpoint=(dist_files.handle_index, ())),
        routing.Rule("/<path:_>", endpoint=(dist_files.handle, ())),
    ])
    def app(env, start_resp):
        urls = routes.bind_to_environ(env)
        try:
            (handler, args), kw = urls.match()
        except HTTPException as e:
            return e(env, start_resp)
        else:
            args = (Request(env),) + args
            kw = _del_underscore_vars(kw)
            try:
                return handler(*args, **kw)(env, start_resp)
            except HTTPException as e:
                return e(env, start_resp)
    return app

def _del_underscore_vars(kw):
    return {
        k: kw[k] for k in kw if k[0] != "_"
    }

def _handle_runs(req, data):
    return _json_resp(data.runs(req.args))

def _handle_config(req, data):
    return _json_resp(data.config(req.args))

def _json_resp(data):
    return Response(
        json.dumps(data),
        content_type="application/json",
        headers=[("Access-Control-Allow-Origin", "*")])
