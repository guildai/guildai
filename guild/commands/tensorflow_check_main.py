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

import os
import re
import subprocess
import sys

import click

class State(object):
    errors = False

def _warn(msg):
    return click.style(msg, fg="red", bold=True)

def print_info():
    state = State()
    _print_tensorflow_info(state)
    _print_tensorboard_info(state)
    _print_cuda_info()
    if state.errors:
        sys.exit(1)

def _print_tensorflow_info(state):
    try:
        import tensorflow as tf
    except ImportError as e:
        state.errors = True
        click.echo("tensorflow_version:        %s" % _warn("Not installed"))
        click.echo(_normalize_import_error_msg(e), err=True)
    else:
        click.echo("tensorflow_version:        %s" % _tf_version(tf, state))
        click.echo("tensorflow_cuda_support:   %s" % _cuda_support(tf))
        click.echo("tensorflow_gpu_available:  %s" % _gpu_available(tf, state))

def _tf_version(tf, state):
    try:
        return tf.__version__
    except AttributeError as e:
        state.errors = True
        return _warn("ERROR (%s)" % e)

def _print_tensorboard_info(state):
    try:
        import tensorboard.version as version
    except ImportError as e:
        state.errors = True
        click.echo("tensorboard_version:       %s" % _warn("Not installed"))
        click.echo(_normalize_import_error_msg(e), err=True)
    else:
        click.echo("tensorboard_version:       %s" % version.VERSION)

def _cuda_support(tf):
    if tf.test.is_built_with_cuda():
        return "yes"
    else:
        return "no"

def _gpu_available(tf, state):
    if tf.test.is_gpu_available():
        return "yes"
    elif tf.test.is_built_with_cuda():
        state.errors = True
        return _warn("NO (CUDA support is enabled but GPU is not available)")
    else:
        return "no"

def _print_cuda_info():
    if sys.platform == "darwin":
        _print_macos_cuda_info()
    else:
        _print_linux_cuda_info()

def _print_macos_cuda_info():
    patterns = [
        ("libcuda", "libcuda\\.([\\S]+)\\.so\\.dylib"),
        ("libcudnn", "libcudnn\\.([\\S]+)\\.dylib"),
    ]
    try:
        raw = subprocess.check_output(["mmap", str(os.getpid())])
    except OSError:
        raw = ""
    _gen_print_lib_info(patterns, raw)

def _print_linux_cuda_info():
    patterns = [
        ("libcuda", "libcuda\\.so\\.([\\S]+)"),
        ("libcudnn", "libcudnn\\.so\\.([\\S]+)"),
    ]
    proc_maps = "/proc/%s/maps" % os.getpid()
    if not os.path.exists(proc_maps):
        return
    try:
        raw = open(proc_maps, "r").read()
    except IOError:
        raw = ""
    _gen_print_lib_info(patterns, raw)

def _gen_print_lib_info(patterns, raw):
    for name, pattern in patterns:
        m = re.search(pattern, raw)
        space = " " * (18 - len(name))
        if m:
            click.echo("%s_version:%s%s" % (name, space, m.group(1)))
        else:
            click.echo("%s_version:%snot loaded" % (name, space))

def _normalize_import_error_msg(e):
    msg = str(e)
    m = re.match("No module named ([^']+)", msg)
    if m:
        return "No module named '%s'" % m.group(1)
    return msg

if __name__ == "__main__":
    print_info()
