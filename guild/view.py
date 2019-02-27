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

import logging
import os
import socket
import subprocess
import sys
import threading
import time

import requests

from werkzeug.exceptions import NotFound
from werkzeug.utils import redirect

import guild.index

from guild import serving_util
from guild import util
from guild import var

log = logging.getLogger("guild")

MODULE_DIR = os.path.dirname(__file__)

TB_RUNS_MONITOR_INTERVAL = 5
TB_REFRESH_INTERVAL = 5

SCALAR_KEYS = [
    ("step", (
        # For loss
        "loss_step",
        "total_loss_1_step",
        "train/loss_step",
        "train/loss_1_step",
        "train/cross_entropy_1_step",
        "train/total_loss_1_step",
        "logs/train/loss_step",
        "logs/train/cross_entropy_1_step",
        "logs/train/total_loss_1_step",
        "model/loss_step",
        "model/cross_entropy_1_step",
        "model/total_loss_1_step",
        "OptimizeLoss_step",
        "epoch_loss_step",
        # For accuracy
        "val_acc_step",
        "validate/accuracy_step",
        "validation/accuracy_1_step",
        "logs/validation/accuracy_1_step",
        "eval/accuracy_step",
        "eval/Accuracy_step",
        "acc_step",
        "epoch_acc_step",
        "eval/DetectionBoxes_Precision/mAP_step",
    )),
    ("loss", (
        "loss",
        "total_loss_1",
        "train/loss",
        "train/loss_1",
        "train/cross_entropy_1",
        "train/total_loss_1",
        "logs/train/loss",
        "logs/train/cross_entropy_1",
        "logs/train/total_loss_1",
        "model/loss",
        "model/cross_entropy_1",
        "model/total_loss_1",
        "OptimizeLoss",
        "epoch_loss",
    )),
    ("val_acc", (
        "val_acc",
        "validate/accuracy",
        "validation/accuracy_1",
        "logs/validation/accuracy_1",
        "eval/accuracy",
        "eval/Accuracy",
        "acc",
        "epoch_acc",
        "eval/DetectionBoxes_Precision/mAP",
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
        self._view_base_url = util.local_server_url(host, view_port)
        self._ready = False

    def run(self):
        args = [
            self._devserver_bin(),
            "--host", self.host,
            "--config", self._devserver_config(),
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
        url_base = util.local_server_url(self.host, self.port)
        while not self._ready:
            ping_url = "{}/assets/favicon.png".format(url_base)
            try:
                requests.get(ping_url)
            except requests.exceptions.ConnectionError:
                time.sleep(0.1)
            else:
                self._ready = True

    @staticmethod
    def _devserver_bin():
        path = os.path.join(
            MODULE_DIR, "view/node_modules/.bin/webpack-dev-server")
        if not os.path.exists(path):
            raise AssertionError(
                "{} does not exits - did you resolve node dependencies by "
                "running npm install?".format(path))
        return path

    @staticmethod
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
        self._monitor = util.RunsMonitor(
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
        return self._tb

    def iter_servers(self):
        for key in self._servers:
            yield self._servers[key]

    def stop_servers(self):
        for server in self._servers.values():
            if server.running:
                log.debug("stopping TensorBoard server (%s)", server)
                server.stop()

class DistFiles(serving_util.StaticDir):

    def __init__(self):
        dist_dir = os.path.join(MODULE_DIR, "view/dist")
        super(DistFiles, self).__init__(dist_dir)

class RunFiles(serving_util.StaticBase):

    def __init__(self):
        super(RunFiles, self).__init__({"/files": var.runs_dir()})

    def handle(self, _req):
        def app(env, start_resp0):
            def start_resp(status, headers):
                headers.append(("Access-Control-Allow-Origin", "*"))
                start_resp0(status, headers)
            return self._app(env, start_resp)
        return app

class RunOutput(object):

    def __init__(self):
        self._output_run_id = None
        self._output = None

    def handle(self, req, run):
        self._ensure_output(run)
        start = req.args.get("s", None, int)
        end = req.args.get("e", None, int)
        lines = [
            (time, stream, line)
            for time, stream, line in self._output.read(start, end)
        ]
        return serving_util.json_resp(lines)

    def _ensure_output(self, run_id):
        if self._output_run_id == run_id:
            return
        run_dir = os.path.join(var.runs_dir(), run_id)
        if not os.path.exists(run_dir):
            raise NotFound()
        self._output = util.RunOutputReader(run_dir)
        self._output_run_id = run_id

def serve_forever(data, host, port, no_open=False, dev=False, logging=False):
    if dev:
        _serve_dev(data, host, port, no_open, logging)
    else:
        _serve_prod(data, host, port, no_open, logging)

def _serve_dev(data, host, port, no_open, logging):
    view_port = util.free_port()
    dev_server = DevServer(host, port, view_port)
    dev_server.start()
    dev_server.wait_for_ready()
    view_url = util.local_server_url(host, view_port)
    if not no_open:
        util.open_url(util.local_server_url(host, port))
    sys.stdout.write(" I  Guild View backend: {}\n".format(view_url))
    _start_view(data, host, view_port, logging)
    sys.stdout.write("\n")

def _serve_prod(data, host, port, no_open, logging):
    view_url = util.local_server_url(host, port)
    if not no_open:
        try:
            util.open_url(view_url)
        except util.URLOpenError:
            sys.stdout.write("Unable to open browser window for Guild View\n")
    sys.stdout.write("Running Guild View at {}\n".format(view_url))
    _start_view(data, host, port, logging)
    sys.stdout.write("\n")

def _start_view(data, host, port, logging):
    tb_servers = TBServers(data)
    index = guild.index.RunIndex()
    app = _view_app(data, tb_servers, index)
    server = serving_util.make_server(host, port, app, logging)
    sys.stdout.flush()
    server.serve_forever()
    tb_servers.stop_servers()

def _view_app(data, tb_servers, index):
    dist_files = DistFiles()
    run_files = RunFiles()
    run_output = RunOutput()
    routes = serving_util.Map([
        ("/runs", _handle_runs, (data, index)),
        ("/files/<path:_>", run_files.handle, ()),
        ("/runs/<run>/output", run_output.handle, ()),
        ("/config", _handle_config, (data,)),
        ("/tb/", _route_tb, ()),
        ("/tb/<key>/", _handle_tb_index, (tb_servers, data)),
        ("/tb/<key>/<path:_>", _handle_tb, (tb_servers,)),
        ("/", dist_files.handle_index, ()),
        ("/<path:_>", dist_files.handle, ()),
    ])
    return serving_util.App(routes)

def _handle_runs(req, data, index):
    runs_data = _runs_data(req, data)
    _apply_scalars(runs_data, index)
    return serving_util.json_resp(runs_data)

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

def _handle_config(_req, data):
    return serving_util.json_resp(data.config())

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
