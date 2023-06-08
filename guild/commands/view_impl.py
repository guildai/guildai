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
import socket
import threading
import time

from guild import cli
from guild import serving_util
from guild import util

from . import api_serve_impl


class Timeout(Exception):
    pass


def StaticApp(app):
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "view")
    static_app = serving_util.SharedDataMiddleware(app, {"/": static_dir})
    return serving_util.RedirectMiddleware({"/": "/index.html"}, static_app)


class ViewServer(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host or socket.gethostname()
        self.port = port

    def run(self):
        app = StaticApp(api_serve_impl.ApiApp())
        server = serving_util.make_server(self.host, self.port, app)
        server.serve_forever()

    def wait_for_ready(self, timeout=5):
        timeout_at = time.time() + timeout
        ping_url = f"{util.local_server_url(self.host, self.port)}/ping"
        while True:
            if time.time() >= timeout_at:
                raise Timeout()
            try:
                util.http_get(ping_url)
            except util.HTTPConnectionError:
                time.sleep(0.1)
            else:
                break


def main(args):
    host, port = _host_and_port(args)
    server = _start_server(host, port)
    _maybe_open_browser(args, host, port)
    print(
        f"Running Guild View at {util.local_server_url(host, port)} "
        "(Type Ctrl-C to quit)"
    )
    server.join()


def _host_and_port(args):
    return (
        args.host or "0.0.0.0",
        args.port or util.free_port(),
    )


def _start_server(host, port):
    server = ViewServer(host, port)
    server.start()
    try:
        server.wait_for_ready()
    except Timeout:
        cli.error(f"timeout waiting for API server at {host}:{port}")
    else:
        return server


def _maybe_open_browser(args, host, port):
    if args.no_open:
        return
    try:
        util.open_url(util.local_server_url(host, port))
    except util.URLOpenError:
        print("Unable to open browser window for Guild View")
