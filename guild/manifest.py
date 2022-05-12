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

import shlex


class Manifest:
    def __init__(self, path, mode):
        self.path = path
        self._f = open(path, mode + "b")

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def close(self):
        self._f.close()

    def read(self):
        line = self._f.readline()
        if not line:
            raise ValueError("end of file")
        return _decode_line(line)

    def write(self, args):
        self._f.write(_encode_args(args))
        self._f.write(b"\n")
        self._f.flush()

    def __iter__(self):
        for line in self._f:
            yield _decode_line(line)

    def __del__(self):
        try:
            self._f.close()
        except ValueError:
            pass


def _encode_args(args):
    joined = " ".join([shlex.quote(arg) for arg in args])
    return joined.encode("utf-8")


def _decode_line(line):
    decoded = line.decode("utf-8")
    return shlex.split(decoded)
