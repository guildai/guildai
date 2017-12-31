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
from werkzeug.wrappers import Response
from werkzeug.wsgi import SharedDataMiddleware

from guild import util

MODULE_DIR = os.path.dirname(__file__)

class ViewData(object):

    def runs(self):
        raise NotImplementedError()

    def config(self):
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

class StaticApp(object):

    def __init__(self):
        root = os.path.join(MODULE_DIR, "view/dist")
        self._app = SharedDataMiddleware(self._not_found, {"/": root})

    def handle(self):
        return self._app

    def handle_index(self):
        def app(env, start_resp):
            env["PATH_INFO"] = "/index.html"
            return self._app(env, start_resp)
        return app

    @staticmethod
    def _not_found(_env, _start_resp):
        raise NotFound()

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
    static = StaticApp()
    routes = routing.Map([
        routing.Rule("/runs", endpoint=(_handle_runs, (data,))),
        routing.Rule("/config", endpoint=(_handle_config, (data,))),
        routing.Rule("/", endpoint=(static.handle_index, ())),
        routing.Rule("/<path:_>", endpoint=(static.handle, ())),
    ])
    def app(env, start_resp):
        urls = routes.bind_to_environ(env)
        try:
            (handler, args), kw = urls.match()
        except HTTPException as e:
            return e(env, start_resp)
        else:
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

def _handle_runs(data):
    return _json_resp(data.runs() + _fake_runs())

def _handle_config(data):
    return _json_resp(data.config())

def _json_resp(data):
    return Response(
        json.dumps(data),
        content_type="application/json",
        headers=[("Access-Control-Allow-Origin", "*")])

def _fake_runs():
    # pylint: disable=line-too-long
    return [
        _fake_run(
            'e61e0ba2',
            './slim-resnet-v2-152:fine-tune',
            'slim-resnet-v2-152',
            'fine-tune',
            '2017-12-06 11:51:15',
            '2017-12-06 11:51:18',
            'error',
            1,
            '/usr/bin/python -u /home/garrett/SCM/guild/guild/scripts/run slim_op train_image_classifier --model_name resnet_v2_50 --train_dir . --dataset_split_name train --dataset_dir data --checkpoint_path resnet_v2_50.ckpt --checkpoint_exclude_scopes resnet_v2_50/logits --trainable_scopes resnet_v2_50/logits --batch_size 4 --dataset_name flowers --learning_rate 0.01 --learning_rate_decay_type exponential --log_every_n_steps 100 --max_number_of_steps 1000 --optimizer rmsprop --save_interval_secs 60 --save_summaries_secs 60 --weight_decay 4e-05',
            {
                'batch-size': 32,
                'dataset': 'cifar10',
                'learning-rate': 0.01,
                'learning-rate-decay-type': 'exponential',
                'log-every-n-steps': 100,
                'max-steps': 1000,
                'optimizer': 'rmsprop',
                'save-model-secs': 60,
                'save-summaries-secs': 60,
                'weight-decay': 4e-05
            },
            {
                'VTE_VERSION': '4205',
                'WINDOWID': '73400326',
                'WINDOWPATH': '8',
                'XAUTHORITY': '/home/garrett/.Xauthority',
                'XDG_CONFIG_DIRS': '/etc/xdg/xdg-cinnamon:/etc/xdg',
                'XDG_CURRENT_DESKTOP': 'X-Cinnamon',
                'XDG_DATA_DIRS': '/usr/share/cinnamon:/usr/share/gnome:/usr/local/share/:/usr/share/:/usr/share/mdm/',
                'XDG_RUNTIME_DIR': '/run/user/1000',
                'XDG_SEAT': 'seat0',
                'XDG_SESSION_COOKIE': '2a5d5f96ef9147c0b35535562b32d0ff-1512503364.444035-596823101',
                'XDG_SESSION_DESKTOP': 'cinnamon',
                'XDG_SESSION_ID': 'c1',
                'XDG_VTNR': '8'
            },
            [
                {
                    "operation": 'slim.datasets/slim-flowers:prepare',
                    "run": '2f64285c'
                }
            ],
            [
                {"path": 'checkpoint', "type": 'Latest checkpoint marker', "size": 265, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'data', "type": 'Operation output link', "size": None, "icon": 'file-export', "iconTooltip": 'Link'},
                {"path": 'eval.graph', "type": 'Link to resource', "size": None, "icon": 'file-export', "iconTooltip": 'Link'},
                {"path": 'events.out.tfevents.1512527577.omaha', "type": 'TensorFlow event log', "size": 6868836, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'graph.pbtxt', "type": 'TensorFlow graph def', "size": 4140777, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-0.data-00000-of-00001', "type": 'TensorFlow checkpoint values', "size": 94382148, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-0.index', "type": 'TensorFlow checkpoint index', "size": 11499, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-0.meta', "type": 'TensorFlow checkpoint meta graph', "size": 2005581, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-1000.data-00000-of-00001', "type": 'TensorFlow checkpoint values', "size": 94382148, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-1000.index', "type": 'TensorFlow checkpoint index', "size": 11499, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-1000.meta', "type": 'TensorFlow checkpoint meta graph', "size": 2005581, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-258.data-00000-of-00001', "type": 'TensorFlow checkpoint values', "size": 94382148, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-258.index', "type": 'TensorFlow checkpoint index', "size": 11499, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-258.meta', "type": 'TensorFlow checkpoint meta graph', "size": 2005581, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-524.data-00000-of-00001', "type": 'TensorFlow checkpoint values', "size": 94382148, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-524.index', "type": 'TensorFlow checkpoint index', "size": 11499, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-524.meta', "type": 'TensorFlow checkpoint meta graph', "size": 2005581, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-792.data-00000-of-00001', "type": 'TensorFlow checkpoint values', "size": 94382148, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-792.index', "type": 'TensorFlow checkpoint index', "size": 11499, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'model.ckpt-792.meta', "type": 'TensorFlow checkpoint meta graph', "size": 2005581, "icon": 'file', "iconTooltip": 'File'},
                {"path": 'resnet_v2_50.ckpt', "type": 'Resource link', "size": None, "icon": 'file-export', "iconTooltip": 'Link'},
                {"path": 'slim', "type": 'Resource link', "size": None, "icon": 'file-export', "iconTooltip": 'Link'},
                {"path": 'train.graph', "type": 'Resource link', "size": None, "icon": 'file-export', "iconTooltip": 'Link'}
            ]
        ),
        _fake_run(
            '0df943ac',
            './magenta-melody-rnn:compose',
            'magenta-melody-rnn',
            'compose',
            '2017-12-13 13:14:31',
            '2017-12-13 13:14:34',
            'completed',
            0,
            '/usr/bin/python -u /home/garrett/SCM/guild/guild/scripts/run slim_op export_inference_graph --model_name resnet_v1_50 --dataset_dir data --output_file graph.pb --dataset_name custom',
            {},
            {},
            [],
            [
                {"path": '2017-12-06_120417_01.mid', "type": 'Audio', "size": 262, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_02.mid', "type": 'Audio', "size": 153, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_03.mid', "type": 'Audio', "size": 321, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_04.mid', "type": 'Audio', "size": 344, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_05.mid', "type": 'Audio', "size": 298, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_06.mid', "type": 'Audio', "size": 183, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_07.mid', "type": 'Audio', "size": 928, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_08.mid', "type": 'Audio', "size": 372, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_09.mid', "type": 'Audio', "size": 254, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": '2017-12-06_120417_10.mid', "type": 'Audio', "size": 211, "icon": 'file-music', "iconTooltip": 'Audio', "viewer": True},
                {"path": 'attention_rnn.mag', "type": 'Resource link', "size": None, "icon": 'file-export', "iconTooltip": 'Link'}
            ]
        ),
        _fake_run(
            '39d61334',
            './slim-resnet-101:train',
            'slim-resnet-101',
            'train',
            '2017-12-06 11:50:00',
            '2017-12-06 11:50:03',
            'terminated',
            None,
            '/usr/bin/python -u /home/garrett/SCM/guild/guild/scripts/run slim_op train_image_classifier --model_name resnet_v1_101 --train_dir . --dataset_split_name train --dataset_dir data --batch_size 1 --dataset_name flowers --learning_rate 0.01 --learning_rate_decay_type exponential --log_every_n_steps 100 --max_number_of_steps 100 --optimizer rmsprop --save_interval_secs 60 --save_summaries_secs 60 --weight_decay 4e-05',
            {},
            {},
            [],
            [
                {"path": 'arbitrary_style_transfer', "type": 'Resource link', "size": None, "icon": 'file-export', "iconTooltip": 'Link'},
                {"path": 'doge.jpg', "type": 'Image', "size": 262, "icon": 'file-image', "iconTooltip": 'Image', "viewer": True},
                {"path": 'doge_stylized_t1_0.jpg', "type": 'Image', "size": 262, "icon": 'file-image', "iconTooltip": 'Image', "viewer": True},
                {"path": 't1.jpg', "type": 'Image', "size": 262, "icon": 'file-image', "iconTooltip": 'Image', "viewer": True}
            ]
        )
    ]

def _fake_run(short_id, op, op_model, op_name, started, stopped, status,
              exit_status, cmd, flags, env, deps, files):
    return {
        "shortId": short_id,
        "operation": op,
        "opModel": op_model,
        "opName": op_name,
        "started": started,
        "stopped": stopped,
        "status": status,
        "exitStatus": exit_status,
        "command": cmd,
        "flags": flags,
        "env": env,
        "deps": deps,
        "files": files,
    }
