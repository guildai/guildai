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

import json
import logging
import sys
import threading
import time

try:
    from urllib.request import urlopen
except ImportError:
    # pylint: disable=import-error
    from urllib2 import urlopen

from guild import util

log = logging.getLogger("guild")

def start_tester(host, port, exit=None):
    if exit is None:
        exit = lambda _code: None
    tester = threading.Thread(target=_test_view, args=(host, port, exit))
    tester.start()

def _test_view(host, port, exit):
    view_url = util.local_server_url(host, port)
    try:
        _wait_for(view_url)
        _test_runs(view_url)
        _test_tensorboard(view_url)
    except Exception:
        log.exception("testing %s", view_url)
        exit(1)
    else:
        exit(0)

def _wait_for(url):
    _urlread(url)

def _test_runs(view_url):
    runs_url = "{}/runs".format(view_url)
    sys.stdout.write("Testing %s\n" % runs_url)
    runs_str = _urlread(runs_url)
    runs = json.loads(runs_str.decode())
    sys.stdout.write(" - Got %i Guild run(s)\n" % len(runs))
    sys.stdout.flush()

def _test_tensorboard(view_url):
    tb_init_url = "{}/tb/0/".format(view_url)
    sys.stdout.write("Initializing TensorBoard at %s\n" % tb_init_url)
    _urlread(tb_init_url)
    runs_url = "{}/tb/0/data/runs".format(view_url)
    sys.stdout.write("Testing %s\n" % runs_url)
    runs_str = _urlread(runs_url)
    runs = json.loads(runs_str.decode())
    sys.stdout.write(" - Got %i TensorBoard run(s)\n" % len(runs))
    sys.stdout.flush()

def _urlread(url):
    timeout = time.time() + 5 # 5 seconds to connect
    while time.time() < timeout:
        try:
            f = urlopen(url)
        except Exception as e:
            if 'refused' not in str(e):
                raise
            time.sleep(1)
        else:
            return f.read()
    raise RuntimeError("connect timeout")
