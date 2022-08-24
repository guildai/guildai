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

from shlex import quote as q


class ParseError(Exception):
    pass


class Select:
    def __init__(self, cols):
        self.cols = cols

    def __repr__(self):
        return f"<guild.query.Select {[str(c) for c in self.cols]}>"


class Col:

    named_as = None

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__name__} {self}>"

    def __str__(self):
        raise NotImplementedError()

    def _as_suffix(self):
        return f" as {q(self.named_as)}" if self.named_as else ""

    @property
    def header(self):
        return self.named_as or str(self)


class Scalar(Col):
    def __init__(self, key, qualifier=None, step=False):
        self.key = key
        self.qualifier = qualifier
        self.step = step

    def __str__(self):
        qual = f"{self.qualifier} " if self.qualifier else ""
        step = " step" if self.step else ""
        return f"scalar:{qual}{self.key}{step}{self._as_suffix()}"

    @property
    def header(self):
        if self.named_as:
            return self.named_as
        key = self.key.replace("#", " ").strip()
        step = " step" if self.step else ""
        return f"{key}{step}"

    def split_key(self):
        parts = self.key.split("#", 1)
        if len(parts) == 2:
            return parts
        return None, parts[0]


class Attr(Col):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"attr:{self.name}{self._as_suffix()}"

    @property
    def header(self):
        return self.named_as or self.name


class Flag(Col):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"flag:{self.name}{self._as_suffix()}"

    @property
    def header(self):
        return self.named_as or self.name


def parse(s):
    from . import qparse

    p = qparse.parser()
    return p.parse(s)


def parse_colspec(colspec):
    assert isinstance(colspec, str), colspec
    return parse(f"select {colspec}")
