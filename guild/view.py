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

import sys
import threading

from cefpython3 import cefpython as cef
from werkzeug import serving

class Server(threading.Thread):

    def __init__(self, app, host, port):
        super(Server, self).__init__()
        self.app = app
        self.host = host
        self.port = port
        self._server = None

    def run(self):
        self._server = serving.make_server(
            self.host,
            self.port,
            self.app,
            threaded=True)
        self._server.serve_forever()

    def stop(self):
        assert self._server
        self._server.shutdown()

def serve_forever(host, port):
    server = _start_backend(host, port)
    _start_frontend(host, port)
    server.stop()

def _start_backend(host, port):
    app = _init_wsgi_app()
    server = Server(app, host, port)
    server.start()
    return server

def _init_wsgi_app():
    def app(_env, start_resp):
        start_resp("200 OK", {})
        return ["Hello Guild View!"]
    return app

def _start_frontend(host, port):
    sys.excepthook = cef.ExceptHook
    cef.Initialize()
    url = "http://{}:{}".format(host or "localhost", port)
    cef.CreateBrowserSync(url=url, window_title="Guild View")
    cef.MessageLoop()
    cef.Shutdown()
