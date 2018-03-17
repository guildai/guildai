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

from tensorflow.python.saved_model import loader_impl

def model_info(saved_model_path):
    sm = loader_impl._parse_saved_model(saved_model_path)
    return [_meta_graph_info(mg) for mg  in sm.meta_graphs]

def _meta_graph_info(mg):
    return {
        "tags": list(mg.meta_info_def.tags),
        "tensorflow_version": mg.meta_info_def.tensorflow_version,
        "tensorflow_git_version": mg.meta_info_def.tensorflow_git_version,
        "signature": _meta_graph_signature_info(mg),
    }

def _meta_graph_signature_info(mg):
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
        "shape": _tensor_shape_info(t.tensor_shape)
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

def serve_forever(saved_model_path, host, port):
    print("TODO: serve it!", saved_model_path, host, port)
