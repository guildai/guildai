# Copyright 2017-2022 RStudio, PBC
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

from guild import cli


def inspect_checkpoint(args):
    _check_tensorflow()
    if args.file_name.endswith(".pb"):
        _inspect_graph(args)
    else:
        _inspect_checkpoint(args)


def _check_tensorflow():
    try:
        import tensorflow as _unused
    except ImportError as e:
        _handle_tensorflow_import_error(e)


def _handle_tensorflow_import_error(e):
    if "tensorflow" in str(e):
        cli.out(
            "TensorFlow is not installed.\n"
            "Refer to https://www.tensorflow.org/install/ for help "
            "installing TensorFlow on your system.",
            err=True,
        )
    else:
        cli.out(f"Error loading TensorBoard: {e}", err=True)
    cli.error()


def _inspect_graph(args):
    graph = _load_graph(args.file_name)
    for op in graph.get_operations():
        sys.stdout.write(f"{op.name}\n")
        for out in op.outputs:
            sys.stdout.write(f"{out.name}\n")


def _load_graph(filename):
    # pylint: disable=import-error
    import tensorflow as tf

    graph = tf.Graph()
    sess = tf.Session(graph=graph)
    with tf.gfile.FastGFile(filename, "rb") as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        with sess.graph.as_default():
            tf.import_graph_def(graph_def)
    return graph


def _inspect_checkpoint(args):
    # pylint: disable=import-error,no-name-in-module
    from tensorflow.python.tools import inspect_checkpoint as inspect

    inspect.FLAGS = args
    inspect.main([])
