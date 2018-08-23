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

import time

from . import service_impl_support

NAME = "s3-sync"
TITLE = "S3 sync service"

def start(args):
    sync = lambda log: _sync(args, log)
    service_impl_support.start(NAME, sync, args, TITLE)

def _sync(_args, log):
    log.info("%s started" % TITLE)
    while True:
        log.info("Sync it up kid, you earned it!")
        time.sleep(2)

def stop():
    service_impl_support.stop(NAME, TITLE)

def status():
    service_impl_support.status(NAME, TITLE)
