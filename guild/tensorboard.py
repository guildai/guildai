from __future__ import absolute_import

import errno
import os
import socket
import sys

import tensorflow as tf
from werkzeug import serving

from tensorboard import util
from tensorboard import version
from tensorboard.backend import application
from tensorboard.plugins.audio import audio_plugin
from tensorboard.plugins.core import core_plugin
from tensorboard.plugins.distribution import distributions_plugin
from tensorboard.plugins.graph import graphs_plugin
from tensorboard.plugins.histogram import histograms_plugin
from tensorboard.plugins.image import images_plugin
from tensorboard.plugins.pr_curve import pr_curves_plugin
from tensorboard.plugins.profile import profile_plugin
from tensorboard.plugins.projector import projector_plugin
from tensorboard.plugins.scalar import scalars_plugin
from tensorboard.plugins.text import text_plugin

DEFAULT_RELOAD_INTERVAL = 5

def create_app(plugins, logdir, reload_interval):
    return application.standard_tensorboard_wsgi(
        assets_zip_provider=None,
        db_uri="",
        logdir=os.path.expanduser(logdir),
        purge_orphaned_data=False,
        reload_interval=reload_interval,
        plugins=plugins,
        path_prefix="")

def make_simple_server(app, host, port):
    server = serving.make_server(host, port, app, threaded=True)
    final_host = socket.gethostname()
    server.daemon_threads = True
    server.handle_error = _handle_error
    final_port = server.socket.getsockname()[1]
    tensorboard_url = "http://%s:%d" % (final_host, final_port)
    return server, tensorboard_url

def run_simple_server(tb_app, host, port):
    server, url = make_simple_server(tb_app, host, port)
    sys.stderr.write(
        "TensorBoard %s at %s (Press CTRL+C to quit)\n"
        % (version.VERSION, url))
    sys.stderr.flush()
    server.serve_forever()

def _handle_error(unused_request, client_address):
    exc_info = sys.exc_info()
    e = exc_info[1]
    if isinstance(e, IOError) and e.errno == errno.EPIPE:
        tf.logging.warn('EPIPE caused by %s:%d in HTTP serving' % client_address)
    else:
        tf.logging.error('HTTP serving error', exc_info=exc_info)

def main(logdir, host, port, reload_interval=DEFAULT_RELOAD_INTERVAL):
    util.setup_logging()
    plugins = [
        core_plugin.CorePlugin,
        scalars_plugin.ScalarsPlugin,
        images_plugin.ImagesPlugin,
        audio_plugin.AudioPlugin,
        graphs_plugin.GraphsPlugin,
        distributions_plugin.DistributionsPlugin,
        histograms_plugin.HistogramsPlugin,
        pr_curves_plugin.PrCurvesPlugin,
        projector_plugin.ProjectorPlugin,
        text_plugin.TextPlugin,
        profile_plugin.ProfilePlugin,
    ]
    app = create_app(plugins, logdir, reload_interval)
    run_simple_server(app, host, port)
