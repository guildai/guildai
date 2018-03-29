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
import sys
import threading
import time

try:
    from urllib.request import urlopen
    from urllib.request import Request
except ImportError:
    # pylint: disable=import-error
    from urllib2 import urlopen
    from urllib2 import Request

from guild import util

log = logging.getLogger("guild")

CONNECT_TIMEOUT = 20 # seconds

def start_tester(host, port, sig_key, json_instances, exit=None):
    if exit is None:
        exit = lambda _code: None
    tester = threading.Thread(
        target=_test_serve,
        args=(host, port, sig_key, json_instances, exit))
    tester.start()

def _test_serve(host, port, sig_key, json_instances, exit):
    view_url = util.local_server_url(host, port)
    try:
        _wait_for_server(view_url, CONNECT_TIMEOUT)
        _test_endpoint("{}/{}".format(view_url, sig_key), json_instances)
    except Exception as e:
        time.sleep(1) # allow serve to log its errors
        if hasattr(e, "read"):
            log.error(e.read())
        else:
            log.exception("testing %s", view_url)
        exit(1)
    else:
        exit(0)

def _wait_for_server(url, timeout):
    timeout = time.time() + timeout
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

def _test_endpoint(endpoint, json_instances):
    instances = []
    for line in open(json_instances, "r").readlines():
        instances.append(json.loads(line))
    body = json.dumps({"instances": instances}).encode()
    sys.stdout.write("Testing %s\n" % endpoint)
    req = Request(endpoint, body, {'Content-Type': 'application/json'})
    resp = urlopen(req)
    resp_parsed = json.loads(resp.read().decode())
    sys.stdout.write(
        json.dumps(
            resp_parsed,
            separators=(",", ": "),
            indent=2,
            sort_keys=True))
    sys.stdout.flush()
