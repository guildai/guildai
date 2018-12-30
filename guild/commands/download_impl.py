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

import logging

from guild import cli
from guild import pip_util
from guild import resolver
from guild import resourcedef
from guild import util

log = logging.getLogger("guild")

def main(args):
    resdef = resourcedef.ResourceDef("download", {})
    source = resourcedef.ResourceSource(resdef, args.url)
    download_dir = resolver.url_source_download_dir(source)
    util.ensure_dir(download_dir)
    try:
        source_path = pip_util.download_url(source.uri, download_dir)
    except Exception as e:
        _handle_download_error(e, source)
    else:
        sha256 = util.file_sha256(source_path, use_cache=False)
        print("{}  {}".format(sha256, source_path))

def _handle_download_error(e, source):
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.exception("downloading %s", source)
    cli.error("error downloading %s: %s" % (source, e))
