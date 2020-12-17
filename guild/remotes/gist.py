# Copyright 2017-2020 TensorHub, Inc.
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

from guild import remote as remotelib

from . import meta_sync

log = logging.getLogger("guild.remotes.gist")


class GistRemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return GistRemote(name, config)

    def remote_for_spec(self, spec):
        name = "gist:%s" % spec
        config = remotelib.RemoteConfig({})
        return GistRemote(name, config)


class GistRemote(meta_sync.MetaSyncRemote):
    def __init__(self, name, _config):
        self.name = name
        self.local_sync_dir = meta_sync.local_meta_dir(name, "")
        runs_dir = os.path.join(self.local_sync_dir, "runs")
        super(GistRemote, self).__init__(runs_dir, None)

    def _sync_runs_meta(self, force=False):
        raise NotImplementedError()

    def _delete_runs(self, runs, permanent):
        raise NotImplementedError()

    def _retore_runs(self, runs):
        raise NotImplementedError()

    def _purge_runs(self, runs):
        raise NotImplementedError()

    def push(self, runs, delete=False):
        raise remotelib.OperationNotSupported()

    def pull(self, runs, delete=False):
        raise remotelib.OperationNotSupported()

    def label_runs(self, **opts):
        raise remotelib.OperationNotSupported()  # TODO

    def run_op(self, opspec, flags, restart, no_wait, stage, **opts):
        raise remotelib.OperationNotSupported()

    def watch_run(self, **opts):
        raise remotelib.OperationNotSupported()

    def check(self, **opts):
        raise remotelib.OperationNotSupported()

    def stop_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def cat(self, **opts):
        raise remotelib.OperationNotSupported()

    def comment_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def diff_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def list_files(self, **opts):
        raise remotelib.OperationNotSupported()

    def one_run(self, run_id_prefix):
        raise remotelib.OperationNotSupported()

    def tag_runs(self, **opts):
        raise remotelib.OperationNotSupported()
