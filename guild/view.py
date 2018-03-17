# Copyright 2017-2018 TensorHub, Inc.
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

import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time

import requests

from werkzeug import routing
from werkzeug import serving
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware

import guild.index

from guild import util
from guild import var

log = logging.getLogger("guild")

MODULE_DIR = os.path.dirname(__file__)

TB_RUNS_MONITOR_INTERVAL = 5
TB_REFRESH_INTERVAL = 5

SCALAR_KEYS = [
    ("step", (
        "loss_step",
        "train/loss_step",
        "total_loss_1_step"
    )),
    ("loss", (
        "loss",
        "train/loss",
        "total_loss_1"
    )),
    ("val_acc", (
        "val_acc",
        "validate/accuracy",
        "eval/accuracy",
        "eval/Accuracy",
    ))
]

class ViewData(object):

    def runs(self):
        """Returns a list of unformatted runs.
        """
        raise NotImplementedError()

    def runs_data(self):
        """Returns a list of formatted runs data.
        """
        raise NotImplementedError()

    def one_run(self, run_id_prefix):
        """Returns one unformatted run for a run ID prefix.

        The scope must be extended to all runs - not just runs per the
        current filter.

        If a run doesn't exist that matches `run_id_prefix` returns None.
        """

    def one_run_data(self, run_id_prefix):
        """Returns a formatted run for a run ID prefix.

        If a run doesn't exist that matches `run_id_prefix` returns None.
        """
        raise NotImplementedError()

    def config(self):
        """Returns dict of config for request params.

        Config dict must contain:

          cwd         string  Cwd used for runs
          titleLabel  string  Label suitable for browser title
          version     string  Guild version

        """
        raise NotImplementedError()

class DevServer(threading.Thread):

    def __init__(self, host, port, view_port):
        super(DevServer, self).__init__()
        self.host = host or socket.gethostname()
        self.port = port
        self.view_port = view_port
        self._view_base_url = _view_url(host, view_port)
        self._ready = False

    def run(self):
        args = [
            _devserver_bin(),
            "--host", self.host,
            "--config", _devserver_config(),
            "--progress",
        ]
        env = {
            "HOST": self.host,
            "PORT": str(self.port),
            "VIEW_BASE": self._view_base_url,
            "PATH": os.environ["PATH"],
        }
        p = subprocess.Popen(args, env=env)
        p.wait()

    def wait_for_ready(self):
        url_base = _view_url(self.host, self.port)
        while not self._ready:
            ping_url = "{}/assets/favicon.png".format(url_base)
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

class TBServer(object):

    def __init__(self, tensorboard, key, data):
        self._tb = tensorboard
        self._key = key
        self._data = data
        self.log_dir = None
        self._monitor = None
        self._app = None
        self._started = False

    @property
    def running(self):
        return self._started

    def start(self):
        if self._started:
            raise RuntimeError("already started")
        self.log_dir = util.mktempdir("guild-tensorboard-")
        self._monitor = self._tb.RunsMonitor(
            self._list_runs,
            self.log_dir,
            TB_RUNS_MONITOR_INTERVAL)
        self._monitor.start()
        self._app = self._tb.create_app(
            self.log_dir,
            TB_REFRESH_INTERVAL,
            path_prefix=self._path_prefix())
        self._started = True

    def _list_runs(self):
        if self._key == "0":
            return self._data.runs()
        else:
            run = self._data.one_run(self._key)
            if not run:
                return []
            return [run]

    def _path_prefix(self):
        return "/tb/{}/".format(self._key)

    def __call__(self, env, start_resp):
        if not self.running:
            raise RuntimeError("not started")
        assert self._app
        return self._app(env, start_resp)

    def stop(self):
        if not self._started:
            raise RuntimeError("not started")
        self._monitor.stop()
        util.rmtempdir(self.log_dir)

class TBServers(object):

    def __init__(self, data):
        self._lock = threading.Lock()
        self._servers = {}
        self._data = data
        self._tb = None

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, *_exc):
        self._lock.release()

    def __getitem__(self, key):
        return self._servers[key]

    def start_server(self, key, _run=None):
        tensorboard = self._ensure_tensorboard()
        server = TBServer(tensorboard, key, self._data)
        log.debug("starting TensorBoard server (%s)", server)
        server.start()
        self._servers[key] = server
        log.debug(
            "using log dir %s for TensorBoard server (%s)",
            server.log_dir, server)
        return server

    def _ensure_tensorboard(self):
        if self._tb is None:
            from guild import tensorboard
            self._tb = tensorboard
            self._tb.setup_logging()
        return self._tb

    def iter_servers(self):
        for key in self._servers:
            yield self._servers[key]

    def stop_servers(self):
        for server in self._servers.values():
            if server.running:
                log.debug("stopping TensorBoard server (%s)", server)
                server.stop()

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
    if dev:
        _serve_dev(data, host, port, no_open)
    else:
        _serve_prod(data, host, port, no_open)

def _serve_dev(data, host, port, no_open):
    view_port = util.free_port()
    dev_server = DevServer(host, port, view_port)
    dev_server.start()
    dev_server.wait_for_ready()
    view_url = _view_url(host, view_port)
    if not no_open:
        util.open_url(view_url)
    sys.stdout.write(" I  Guild View backend: {}\n".format(view_url))
    _start_view(data, host, view_port)
    sys.stdout.write("\n")

def _serve_prod(data, host, port, no_open):
    view_url = util.local_server_url(host, port)
    if not no_open:
        util.open_url(view_url)
    sys.stdout.write("Running Guild View at {}\n".format(view_url))
    _start_view(data, host, port)
    sys.stdout.write("\n")

def _start_view(data, host, port):
    tb_servers = TBServers(data)
    index = guild.index.RunIndex()
    app = _view_app(data, tb_servers, index)
    try:
        server = serving.make_server(host, port, app, threaded=True)
    except socket.error as e:
        if host:
            raise
        log.debug(
            "error starting server on %s:%s (%s), "
            "trying IPv6 default host '::'",
            host, port, e)
        server = serving.make_server("::", port, app, threaded=True)
    sys.stdout.flush()
    server.serve_forever()
    tb_servers.stop_servers()

def _view_app(data, tb_servers, index):
    dist_files = DistFiles()
    run_files = RunFiles()
    def rule(path, handler, *args):
        return routing.Rule(path, endpoint=(handler, args))
    routes = routing.Map([
        rule("/runs", _handle_runs, data, index),
        rule("/runs/<path:_>", run_files.handle),
        rule("/config", _handle_config, data),
        rule("/tb/", _route_tb),
        rule("/tb/<key>/", _handle_tb_index, tb_servers, data),
        rule("/tb/<key>/<path:_>", _handle_tb, tb_servers),
        rule("/", dist_files.handle_index),
        rule("/<path:_>", dist_files.handle),
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

def _handle_runs(req, data, index):
    runs_data = _runs_data(req, data)
    _apply_scalars(runs_data, index)
    return _json_resp(runs_data)

def _runs_data(req, data):
    try:
        run_id_prefix = req.args["run"]
    except KeyError:
        return data.runs_data()
    else:
        return [_one_run_data(run_id_prefix, data)]

def _one_run_data(run_id_prefix, data):
    data = data.one_run_data(run_id_prefix)
    if not data:
        raise NotFound()
    return data

def _apply_scalars(runs_data, index):
    run_ids = [run["id"] for run in runs_data]
    scalars = _run_scalars(run_ids, index)
    for run in runs_data:
        run["scalars"] = scalars[run["id"]]

def _run_scalars(run_ids, index):
    scalars = {}
    for run_result in index.runs(run_ids):
        run_scalars = scalars.setdefault(run_result.id, {})
        for normalized_key, possible_keys in SCALAR_KEYS:
            val = run_result.scalar(possible_keys)
            if val is not None:
                run_scalars[normalized_key] = val
    return scalars

def _json_resp(data):
    return Response(
        json.dumps(data),
        content_type="application/json",
        headers=[("Access-Control-Allow-Origin", "*")])

def _handle_config(_req, data):
    return _json_resp(data.config())

def _route_tb(req):
    if "run" in req.args:
        key = req.args["run"]
    else:
        key = "0"
    return redirect("/tb/{}/".format(key), code=303)

def _handle_tb_index(req, tb_servers, data, key):
    try:
        return _handle_tb(req, tb_servers, key)
    except NotFound:
        if key != "0":
            key = _try_run_id(key, data)
        with tb_servers:
            return tb_servers.start_server(key)

def _handle_tb(_req, tb_servers, key):
    with tb_servers:
        try:
            return tb_servers[key]
        except KeyError:
            raise NotFound()

def _try_run_id(key, data):
    run = data.one_run(key)
    if not run:
        raise NotFound()
    return run.id
