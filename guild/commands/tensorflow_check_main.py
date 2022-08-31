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

import os
import re
import subprocess
import sys

import click


class State:
    errors = False


def _warn(msg):
    return click.style(msg, fg="red", bold=True)


def print_info():
    state = State()
    _print_tensorflow_info(state)
    _print_cuda_info()
    if state.errors:
        sys.exit(1)


def _print_tensorflow_info(state):
    try:
        import tensorflow as tf
    except ImportError as e:
        msg = _normalize_import_error_msg(e)
        if msg == "No module named 'tensorflow'":
            click.echo(f"tensorflow_version:        {_warn('not installed')}")
        else:
            click.echo(f"tensorflow_version:        {_warn(f'not installed ({msg})')}")
            state.errors = True
    else:
        click.echo(f"tensorflow_version:        {_tf_version(tf, state)}")
        click.echo(f"tensorflow_cuda_support:   {_cuda_support(tf)}")
        click.echo(f"tensorflow_gpu_available:  {_gpu_available(tf)}")


def _tf_version(tf, state):
    try:
        return tf.__version__
    except AttributeError as e:
        state.errors = True
        return _warn(f"ERROR ({e})")


def _cuda_support(tf):
    if tf.test.is_built_with_cuda():
        return "yes"
    return "no"


def _gpu_available(tf):
    if tf.test.is_gpu_available():
        return "yes"
    if tf.test.is_built_with_cuda():
        return _warn("NO (CUDA support is enabled but GPU is not available)")
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
    proc_maps = f"/proc/{os.getpid()}/maps"
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
        padding = " " * (18 - len(name))
        if m:
            click.echo(f"{name}_version:{padding}{m.group(1)}")
        else:
            click.echo(f"{name}_version:{padding}not loaded")


def _normalize_import_error_msg(e):
    msg = str(e)
    m = re.match("No module named ([^']+)", msg)
    if m:
        return f"No module named '{m.group(1)}'"
    return msg


if __name__ == "__main__":
    print_info()
