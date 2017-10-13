import os
import re

import click

def print_info():
    tf = _try_import_tensorflow()
    if tf is None:
        _handle_tf_not_installed()
    else:
        _print_info(tf)

def _try_import_tensorflow():
    try:
        import tensorflow
    except ImportError as e:
        if e.message != "No module named tensorflow":
            click.echo(_warn("Error importing tensorflow:"))
            click.echo(str(e))
        return None
    else:
        return tensorflow

def _handle_tf_not_installed():
    click.echo("tensorflow_version:        %s" % _warn("NOT INSTALLED"))
    raise SystemExit(1)

def _warn(msg, bold=False):
    return click.style(msg, fg="red", bold=bold)

def _print_info(tf):
    click.echo("tensorflow_version:        %s" % _version(tf))
    click.echo("tensorflow_cuda_support:   %s" % _cuda_support(tf))
    click.echo("tensorflow_gpu_available:  %s" % _gpu_available(tf))
    _print_cuda_info()

def _version(tf):
    return tf.__version__

def _cuda_support(tf):
    return "yes" if tf.test.is_built_with_cuda() else "no"

def _gpu_available(tf):
    return "yes" if tf.test.is_gpu_available() else "no"

def _print_cuda_info():
    proc_maps = "/proc/%s/maps" % os.getpid()
    if not os.path.exists(proc_maps):
        return
    raw = open(proc_maps, "r").read()
    version_patterns = [
        ("libcuda", "libcuda\\.so\\.([\\S]+)"),
        ("libcudnn", "libcudnn\\.so\\.([\\S]+)"),
    ]
    for name, pattern in version_patterns:
        m = re.search(pattern, raw)
        space = " " * (18 - len(name))
        if m:
            click.echo("%s_version:%s%s" % (name, space, m.group(1)))
        else:
            click.echo("%s_version:%snot loaded" % (name, space))

if __name__ == "__main__":
    print_info()
