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
import sys
import threading

from werkzeug.exceptions import HTTPException, MethodNotAllowed

import tensorflow as tf

# pylint: disable=no-name-in-module
from tensorflow.python.saved_model import loader_impl
from tensorflow.core.framework import types_pb2

import guild

from guild import config
from guild import serving_util
from guild import util

log = logging.getLogger("guild")

MODULE_DIR = os.path.dirname(__file__)

class TagsError(Exception):

    def __init__(self, path, tags):
        super(TagsError, self).__init__(path, tags)
        self.path = path
        self.tags = tags

class SessionRun(object):

    def __init__(self, sess, sig, sess_lock):
        self._sess = sess
        self._inputs = [(name, t.name) for name, t in sig.inputs.items()]
        self._outputs = [(name, t.name) for name, t in sig.outputs.items()]
        self._sess_lock = sess_lock

    def __call__(self, req):
        if req.content_type == "application/json":
            return self._handle_json(req.stream)
        elif "json-instances" in req.files:
            return self._handle_json_instances(req.files["json-instances"])
        self._error("missing one of: json body, json-instances file", 400)

    def _handle_json(self, f):
        raw = f.read()
        try:
            parsed = json.loads(raw.decode())
        except ValueError as e:
            self._error("invalid JSON: %s" % e, 400)
        else:
            try:
                instances = parsed["instances"]
            except KeyError:
                self._error("missing 'instances' attr in JSON", 400)
            else:
                return self._run(self._feed_dict(instances))

    def _handle_json_instances(self, f):
        raw = f.read()
        try:
            instances = self._parse_json_instances(raw)
        except json.decoder.JSONDecodeError as e:
            self._error("invalid JSON: %s" % e, 400)
        else:
            return self._run(self._feed_dict(instances))

    @staticmethod
    def _parse_json_instances(s):
        lines = s.split(b"\n")
        return [json.loads(line.decode()) for line in lines if line]

    def _feed_dict(self, instances):
        result = {}
        for inst in instances:
            for name, t_name in self._inputs:
                val = inst.get(name)
                result.setdefault(t_name, []).append(val)
        return result

    def _run(self, feed_dict):
        t_outputs = [t_name for _name, t_name in self._outputs]
        log.debug("running %s with %s", t_outputs, feed_dict)
        try:
            with self._sess_lock:
                result = self._sess.run(t_outputs, feed_dict=feed_dict)
        except tf.errors.OpError as e:
            self._error(str(e), 400)
        except ValueError as e:
            self._error(str(e), 400)
        except Exception as e:
            log.exception(
                "session.run:\n"
                " outputs: %s\n"
                " inputs: %s", t_outputs, feed_dict)
            self._error("unhandled error: %s" % e, 500)
        else:
            return self._format_result(result)

    def _format_result(self, result):
        names = [name for name, _t_name in self._outputs]
        predictions = [
            {name: self._fmt_val(val) for name, val in zip(names, inst)}
            for inst in zip(*result)
        ]
        return {
            "predictions": predictions
        }

    @staticmethod
    def _fmt_val(val):
        def ensure_json_serializable(val):
            if isinstance(val, bytes):
                return val.decode()
            else:
                return val.item()
        if hasattr(val, "__iter__"):
            return [ensure_json_serializable(x) for x in val]
        else:
            return ensure_json_serializable(val)

    @staticmethod
    def _error(msg, code):
        data = {
            "error": {
                "code": code,
                "message": msg,
            }
        }
        resp = serving_util.json_resp(data, code)
        raise HTTPException(response=resp)

class DistFiles(serving_util.StaticDir):

    def __init__(self):
        dist_dir = os.path.join(MODULE_DIR, "serve/dist")
        super(DistFiles, self).__init__(dist_dir)

def model_info(saved_model_path):
    sm = loader_impl._parse_saved_model(saved_model_path)
    return [_meta_graph_info(mg) for mg in sm.meta_graphs]

def _meta_graph_info(mg):
    return {
        "tags": list(mg.meta_info_def.tags),
        "tensorflow_version": mg.meta_info_def.tensorflow_version,
        "tensorflow_git_version": mg.meta_info_def.tensorflow_git_version,
        "signature_defs": _meta_graph_signature_def_info(mg),
    }

def _meta_graph_signature_def_info(mg):
    return {
        key: {
            "method_name": sig.method_name,
            "inputs": _tensor_map_info(sig.inputs),
            "outputs": _tensor_map_info(sig.outputs),
        }
        for key, sig in mg.signature_def.items()
    }

def _tensor_map_info(tm):
    return {
        name: _tensor_info(t)
        for name, t in tm.items()
    }

def _tensor_info(t):
    info = {
        "shape": _tensor_shape_info(t.tensor_shape),
        "dtype": _dtype_name(t.dtype),
    }
    if t.name:
        info["tensor"] = t.name
    elif t.coo_sparse:
        info["coo_sparse"] = {
            "values_tensor": t.coo_sparse.values_tensor_name,
            "indices_tensor": t.coo_sparse.indices_tensor_name,
            "dense_shape_tensor": t.coo_sparse.dense_shape_tensor_name,
        }
    return info

def _tensor_shape_info(shape):
    return [d.size for d in shape.dim]

def _dtype_name(dtype):
    for name, val in types_pb2.DataType.items():
        if val == dtype:
            return name
    raise ValueError("bad dtype: %r" % dtype)

def _meta_graph_for_tags(path, tags):
    tags = set(tags)
    sm = loader_impl._parse_saved_model(path)
    for mg in sm.meta_graphs:
        if set(mg.tags) == tags:
            return mg
    raise LookupError(path, tags)

def serve_forever(saved_model_path, tags, host, port, no_open=False):
    session = _init_session()
    meta_graph = _load_saved_model(saved_model_path, tags, session)
    base_url = util.local_server_url(host, port)
    app = _init_app(meta_graph, session, base_url, saved_model_path)
    server = serving_util.make_server(host, port, app)
    serve_url = util.local_server_url(host, port)
    if not no_open:
        util.open_url(serve_url)
    sys.stdout.write("Running Guild Serve at {}\n".format(serve_url))
    server.serve_forever()
    sys.stdout.write("\n")

def _init_session():
    return tf.Session()

def _load_saved_model(path, tags, session):
    try:
        return loader_impl.load(session, tags, path)
    except RuntimeError as e:
        if "could not be found in SavedModel" in str(e):
            raise TagsError(path, tags)
        raise

def _init_app(meta_graph, sess, base_url, path):
    rules = (
        _signature_rules(meta_graph, sess) +
        _base_rules(meta_graph, base_url, path)
    )
    routes = serving_util.Map(rules)
    return serving_util.App(routes)

def _signature_rules(meta_graph, sess):
    sess_lock = threading.Lock()
    return [
        ("/" + key, _handle_predict, (SessionRun(sess, sig, sess_lock),))
        for key, sig in meta_graph.signature_def.items()
    ]

def _handle_predict(req, run):
    if req.method != "POST":
        raise MethodNotAllowed(valid_methods=["POST"])
    result = run(req)
    return serving_util.json_resp(result)

def _base_rules(meta_graph, base_url, path):
    dist_files = DistFiles()
    return [
        ("/ctx.json", _ctx_app(), ()),
        ("/model.json", _model_app(meta_graph, base_url, path), ()),
        ("/", dist_files.handle_index, ()),
        ("/<path:_>", dist_files.handle, ()),
    ]

def _ctx_app():
    context = {
        "cwd": util.format_dir(config.cwd()),
        "version": guild.__version__,
    }
    def app(_req):
        return serving_util.json_resp(context)
    return app

def _model_app(meta_graph, base_url, path):
    info = _meta_graph_info(meta_graph)
    data = {
        "tags": info["tags"],
        "path": path,
        "tensorflowVersion": info["tensorflow_version"],
        "signatureDefs": [
            {
                "key": key,
                "endpoint": "{}/{}".format(base_url, key),
                "methodName": sig["method_name"],
                "inputs": _tensor_list(sig["inputs"]),
                "outputs": _tensor_list(sig["outputs"]),
            }
            for key, sig in sorted(info["signature_defs"].items())
        ]
    }
    def app(_req):
        return serving_util.json_resp(data)
    return app

def _tensor_list(tensor_dict):
    return [
        {
            "key": key,
            "dtype": t["dtype"],
            "shape": t["shape"],
            "tensor": t["tensor"],
        }
        for key, t in sorted(tensor_dict.items())
    ]
