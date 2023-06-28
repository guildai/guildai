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

import io
import json
import logging
import socket

from werkzeug import routing
from werkzeug import serving
from werkzeug import exceptions
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response

log = logging.getLogger("guild")

HTTPException = exceptions.HTTPException
NotFound = exceptions.NotFound
BadRequest = exceptions.BadRequest


class QuietRequestHandler(serving.WSGIRequestHandler):
    def log(self, type, message, *args):
        if type != 'info':
            super().log(type, message, *args)


class StaticBase:
    def __init__(self, exports):
        self._app = SharedDataMiddleware(self._not_found, exports)

    def handle(self, _req):
        return self._app

    @staticmethod
    def _not_found(_env, _start_resp):
        raise NotFound()


class StaticDir(StaticBase):
    def __init__(self, dir):
        super().__init__({"/": dir})

    def handle_index(self, _req):
        def app(env, start_resp):
            env["PATH_INFO"] = "/index.html"
            return self._app(env, start_resp)

        return app


class RedirectMiddleware:
    def __init__(self, map, app):
        self.map = map
        self.app = app

    def __call__(self, env, start_resp):
        path = env.get("PATH_INFO")
        env["PATH_INFO"] = self.map.get(path, path)
        return self.app(env, start_resp)


def make_server(host, port, app, logging=True):
    if host is None:
        raise RuntimeError("host cannot be None")
    if port is None:
        raise RuntimeError("port cannot be None")
    if logging:
        request_handler = serving.WSGIRequestHandler
    else:
        request_handler = QuietRequestHandler
    try:
        return serving.make_server(
            host,
            port,
            app,
            threaded=True,
            request_handler=request_handler,
        )
    except socket.error as e:
        if host:
            raise
        log.debug(
            "error starting server on %s:%s (%s), trying IPv6 default host '::'", host,
            port, e
        )
        return serving.make_server("::", port, app, threaded=True)


def json_resp(data, status=200, headers=None):
    return Response(
        json.dumps(data),
        status=status,
        content_type="application/json",
        headers=headers or [],
    )


def Rule(path, handler, *args):
    return routing.Rule(path, endpoint=(handler, args))


def Map(rules):
    return routing.Map([Rule(path, handler, *args) for path, handler, args, in rules])


def dispatch(routes, env, start_resp):
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


def _del_underscore_vars(kw):
    return {k: kw[k] for k in kw if k[0] != "_"}


def App(routes, error_handler=None):
    def app(env, start_resp):
        try:
            return dispatch(routes, env, start_resp)
        except Exception as e:
            if error_handler:
                return error_handler(e)(env, start_resp)
            raise

    return app


def request_get(app, url):
    resp = {}

    def start_resp(status, _headers):
        resp["status"] = status

    resp["body"] = app(_request_env("GET", url), start_resp)
    return resp


def _request_env(method, url, body=None, content_type=None):
    from urllib.parse import urlparse

    req = urlparse(url)
    env = {
        "wsgi.url_scheme": "http",
        "REQUEST_METHOD": method,
        "PATH_INFO": req.path,
        "QUERY_STRING": req.query,
    }
    if body is not None:
        env["wsgi.input"] = io.BytesIO(body.encode())
        env["CONTENT_LENGTH"] = str(len(body))
    if content_type:
        env["CONTENT_TYPE"] = content_type
    return env


def request_post(app, url, body, content_type=None):
    # TODO body and content type
    resp = {}

    def start_resp(status, _headers):
        resp["status"] = status

    resp["body"] = app(_request_env("POST", url, body, content_type), start_resp)
    return resp
