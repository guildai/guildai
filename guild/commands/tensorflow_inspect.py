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

import click

from guild import click_util

# NOTE: The args interface here must match that of
# tensorflow/python/tools/inspect_checkpoint.py as it's used directly
# as the FLAGS global for that module.

@click.command("inspect")
@click.argument("file_name", metavar="PATH")
@click.option(
    "--tensor-name", metavar="NAME",
    default="",
    help="Name of the tensor to inspect.")
@click.option(
    "--all-tensors",
    is_flag=True,
    help="Print the values of all the tensors.")
@click.option(
    "--all-tensor-names",
    is_flag=True,
    help="Print the name of all the tensors")

@click_util.use_args

def inspect(args):
    """Inspect a TensorFlow checkpoint or graph.

    `PATH` is the path to the checkpoint file (usually ending in
    ``.ckpt``) or to a protobuf seralized graph (usually ending in
    ``.pb``).

    """
    from . import tensorflow_impl
    tensorflow_impl.inspect_checkpoint(args)
