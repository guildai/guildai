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

import logging
import os
import socket
import time
import warnings

# Avoid expensive imports

from guild import util

log = logging.getLogger("guild")


def tensorboard_version():
    from tensorboard import version

    return version.VERSION


def tensorboard_version_supported():
    major_version = int(tensorboard_version().split(".", 1)[0])
    return major_version >= 2


def Summary(tag, **kw):
    from tensorboard.compat.proto.summary_pb2 import Summary

    return Summary(value=[Summary.Value(tag=tag, **kw)])


def Image(**kw):
    from tensorboard.compat.proto.summary_pb2 import Summary

    return Summary.Image(**kw)


def Event(**kw):
    from tensorboard.compat.proto import event_pb2

    return event_pb2.Event(**kw)


def AsyncWriter(
    logdir, max_queue_size=10, flush_secs=120, filename_base=None, filename_suffix=""
):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        # pylint: disable=no-name-in-module
        from tensorboard.summary.writer import event_file_writer

    filename = event_filename(
        logdir, filename_base=filename_base, filename_suffix=filename_suffix
    )
    record_writer = event_file_writer.RecordWriter(open(filename, "wb"))
    return event_file_writer._AsyncWriter(record_writer, max_queue_size, flush_secs)


def event_filename(logdir, filename_base=None, filename_suffix=""):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        # pylint: disable=no-name-in-module
        from tensorboard.summary.writer import event_file_writer

    filename_base = filename_base or (
        "%010d.%s.%s.%s"
        % (
            time.time(),
            socket.gethostname(),
            os.getpid(),
            event_file_writer._global_uid.get(),
        )
    )
    return (
        os.path.join(logdir, "events.out.tfevents.%s" % filename_base) + filename_suffix
    )


def silence_info_logging():
    from tensorboard.util import tb_logging

    logger = tb_logging.get_logger()
    logger.info = lambda *_args, **_kw: None
    logger.debug = lambda *_args, **_kw: None


def iter_tf_events(dir):
    from tensorboard.backend.event_processing import event_accumulator

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        return event_accumulator._GeneratorFromPath(dir).Load()


def hparams_hp_proto():
    from tensorboard.plugins.hparams import summary_v2 as hp

    return hp


def hparams_api_proto():
    from tensorboard.plugins.hparams import api_pb2

    return api_pb2


def make_ndarray(tensor):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        from tensorboard.util import tensor_util
    return tensor_util.make_ndarray(tensor)


def wsgi_app(
    logdir, plugins, reload_interval=None, path_prefix="", tensorboard_options=None
):
    f = util.find_apply([_wsgi_app_v1_f, _wsgi_app_v2_f, _wsgi_app_unsupported_error])
    return f(
        logdir,
        plugins,
        reload_interval=reload_interval,
        path_prefix=path_prefix,
        tensorboard_options=tensorboard_options,
    )


def _wsgi_app_unsupported_error():
    assert False, tensorboard_version()


def _wsgi_app_v1_f():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        from tensorboard.backend import application
    try:
        standard_tensorboard_wsgi = application.standard_tensorboard_wsgi
    except AttributeError:
        return None
    else:
        return lambda *args, **kw: _wsgi_app_v1(standard_tensorboard_wsgi, *args, **kw)


def _wsgi_app_v1(
    standard_tensorboard_wsgi,
    logdir,
    plugins,
    reload_interval=None,
    path_prefix="",
    tensorboard_options=None,
):
    """WSGI app for tensorboard<2.3.0."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        from tensorboard import program

    tb = program.TensorBoard(plugins)
    argv = _base_tb_args(logdir, reload_interval, path_prefix) + _extra_tb_args(
        tensorboard_options
    )
    log.debug("TensorBoard args: %r", argv)
    tb.configure(argv)
    return standard_tensorboard_wsgi(
        tb.flags, tb.plugin_loaders, tb.assets_zip_provider
    )


def _wsgi_app_v2_f():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        from tensorboard.backend import application
    try:
        TensorBoardWSGIApp = application.TensorBoardWSGIApp
    except AttributeError:
        return None
    else:
        return lambda *args, **kw: _wsgi_app_v2(TensorBoardWSGIApp, *args, **kw)


def _wsgi_app_v2(
    TensorBoardWSGIApp,
    logdir,
    plugins,
    reload_interval=None,
    path_prefix="",
    tensorboard_options=None,
):
    """WSGI app for tensorboard>=2.3.0."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        # pylint: disable=no-name-in-module
        from tensorboard.backend.event_processing import data_ingester
        from tensorboard import program

    tb = program.TensorBoard(plugins)
    argv = _base_tb_args(logdir, reload_interval, path_prefix) + _extra_tb_args(
        tensorboard_options
    )
    log.debug("TensorBoard args: %r", argv)
    tb.configure(argv)

    ingester = data_ingester.LocalDataIngester(tb.flags)
    ingester.start()
    return TensorBoardWSGIApp(
        tb.flags,
        tb.plugin_loaders,
        ingester.data_provider,
        tb.assets_zip_provider,
        ingester.deprecated_multiplexer,
    )


def base_plugins():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Warning)
        from tensorboard import default

    return list(set(default.get_plugins() + default.get_dynamic_plugins()))


def _base_tb_args(logdir, reload_interval, path_prefix):
    args = ["", "--logdir", logdir]
    if reload_interval:
        args.extend(["--reload_interval", str(reload_interval)])
    if path_prefix:
        args.extend(["--path_prefix", path_prefix])
    return args


def _extra_tb_args(options):
    if not options:
        return []
    args = []
    for name, val in sorted(options.items()):
        args.extend(["--%s" % name, str(val)])
    return args


def dark_mode_middleware():
    def f(upstream):
        def app(env, start_resp):
            if env["PATH_INFO"] == "/":
                return _style_tb_for_dark_mode(upstream, env, start_resp)
            elif env["PATH_INFO"] == "/index.js":
                return _disable_dark_mode_toggle(upstream, env, start_resp)
            else:
                return upstream(env, start_resp)

        return app

    return f


def _style_tb_for_dark_mode(upstream, env, start_resp):
    return _apply_middleware_to_plain_text(
        _insert_dark_mode_styles, upstream, env, start_resp
    )


def _apply_middleware_to_plain_text(handle_text, upstream, env, start_resp):
    env["HTTP_ACCEPT_ENCODING"] = "identity"
    start_resp_args = []

    def wrapped_start_resp(status, headers, exc_info):
        start_resp_args.extend([status, headers, exc_info])

    upstream_resp = upstream(env, wrapped_start_resp)
    middleware_resp, content_len = handle_text(upstream_resp)
    start_resp(*_apply_content_len_to_resp(content_len, start_resp_args))
    return middleware_resp


def _insert_dark_mode_styles(resp):
    text = b"".join(resp)

    out = []
    content_len = 0

    def add(part):
        nonlocal content_len
        if part:
            out.append(part)
            content_len += len(part)

    parts = text.split(b"</head>", 1)
    assert len(parts) == 2, parts

    add(parts[0])
    add(
        b"""<style>

html {
  --primary-text-color: #fff !important;
  --primary-background-color: #252526 !important;
  --secondary-text-color: #fff;
  --secondary-background-color: #1e1e1e !important;
  --tb-orange-strong: #1e1e1e !important;
}

body.dark-mode .mat-toolbar {
  background-color: #1e1e1e !important;
}

.tab-bar {
  background-color: #1e1e1e !important;
}


app-header-dark-mode-toggle {
  display: none;
}
</style>
"""
    )
    add(b"</head>")

    parts = parts[1].split(b"<body>", 1)
    assert len(parts) == 2, parts

    add(parts[0])
    add(b"<body class=\"dark-mode\">")
    add(parts[1])

    return out, content_len


def _disable_dark_mode_toggle(upstream, env, start_resp):
    return _apply_middleware_to_plain_text(
        _disable_dark_mode_toggle_scripts, upstream, env, start_resp
    )


def _disable_dark_mode_toggle_scripts(resp):
    text = b"".join(resp)
    text = text.replace(
        b"document.body.classList.toggle(\"dark-mode\"",
        b"document.body.classList.toggle(\"guild-dark-mode\"",
    )

    return [text], len(text)


def _apply_content_len_to_resp(content_len, start_resp_args):
    status, headers, exc_info = start_resp_args
    return [status, _apply_content_len_to_headers(content_len, headers), exc_info]


def _apply_content_len_to_headers(content_len, headers):
    return [_apply_content_len_to_header(content_len, header) for header in headers]


def _apply_content_len_to_header(content_len, header):
    name, _value = header
    return (name, str(content_len)) if name == "Content-Length" else header


def set_notf():
    """Patch tb compat to avoid loading tensorflow.

    TB relies heavily on a tensorflow compatibility layer, which
    prefers to load tensorflow if available. We patch this to force TB
    to use it's own tf-like API to avoid the heavy price of loading
    TF.
    """
    from tensorboard import compat

    # See tensorboard.compat.tf() - uses `notf` to force loading of
    # compat stub rather than tensorflow
    compat.notf = True


if os.getenv("SKIP_NOTF") != "1":
    set_notf()
