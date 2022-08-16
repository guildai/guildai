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


class RemoteLock:
    def __init__(self, remote_name, config):
        self.remote_name = remote_name
        self.config = config


def lock_for_run(run):
    raw = _raw_lock_for_run(run)
    if not raw:
        return None
    remote_name, config = _parse_lock(raw)
    return RemoteLock(remote_name, config)


def _raw_lock_for_run(run):
    try:
        f = open(run.guild_path("LOCK.remote"), "r")
    except IOError:
        return None
    else:
        return f.read().rstrip()


def _parse_lock(raw):
    parts = raw.split(":", 1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]
