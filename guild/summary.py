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

import io
import logging
import re
import sys

import six

log = logging.getLogger("guild")

ALIASES = [
    (re.compile(r"\\key"), "[^ \t]+"),
    (re.compile(r"\\value"), "[0-9\\.e\\-]+"),
]

class SummaryWriter(object):

    def __init__(self, logdir):
        self._logdir = logdir
        self._writer = None

    def add_scalar(self, key, val, step):
        writer = self._get_writer()
        writer.add_scalar(key, val, step)

    def add_image(self, tag, image):
        from PIL import Image
        image = Image.open(image)
        summary = ImageSummary(tag, image)
        self._get_writer().file_writer.add_summary(summary)

    def _get_writer(self):
        if not self._writer:
            from tensorboardX import SummaryWriter
            self._writer = SummaryWriter(self._logdir)
        return self._writer

    def close(self):
        if self._writer:
            self._writer.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

def ImageSummary(tag, image):
    from tensorboardX.proto.summary_pb2 import Summary
    encoded = _encode_png(image)
    summary_image = Summary.Image(
        height=image.height,
        width=image.width,
        colorspace=len(image.getbands()),
        encoded_image_string=encoded)
    return Summary(value=[Summary.Value(tag=tag, image=summary_image)])

def _encode_png(image):
    bytes = io.BytesIO()
    image.save(bytes, format='PNG')
    return bytes.getvalue()

class OutputScalars(object):

    def __init__(self, config, output_dir):
        self._patterns = _init_patterns(config)
        self._writer = SummaryWriter(output_dir)
        self._step = None

    def write(self, line):
        vals = _match_line(line, self._patterns)
        step = vals.pop("step", None)
        if step is not None:
            self._step = step
        if vals:
            for key, val in sorted(vals.items()):
                log.debug("scalar %s val=%s step=%s", key, val, self._step)
                self._writer.add_scalar(key, val, self._step)

    def close(self):
        self._writer.close()

    def print_patterns(self):
        for key, p in self._patterns:
            sys.stdout.write("{}: {}\n".format(key, p.pattern))

def _init_patterns(config):
    if not isinstance(config, list):
        raise TypeError("invalid output scalar config: %r" % config)
    patterns = []
    for item in config:
        patterns.extend(_config_item_patterns(item))
    return patterns

def _config_item_patterns(item):
    if isinstance(item, dict):
        return _map_patterns(item)
    elif isinstance(item, six.string_types):
        return _string_patterns(item)
    else:
        log.warning("invalid item config: %r", item)
        return []

def _map_patterns(map_config):
    patterns = []
    for key, val in sorted(map_config.items()):
        patterns.extend(_compile_patterns(val, key))
    return patterns

def _string_patterns(s):
    return _compile_patterns(s, None)

def _compile_patterns(val, key):
    if not isinstance(val, six.string_types):
        log.warning("invalid output scalar pattern: %r", val)
        return
    val = _replace_aliases(val)
    try:
        p = re.compile(val)
    except Exception as e:
        log.warning("error compiling pattern %s: %s", val, e)
    else:
        yield key, p

def _replace_aliases(val):
    for alias, repl in ALIASES:
        val = alias.sub(repl, val)
    return val

def _match_line(line, patterns):
    vals = {}
    line = _line_to_match(line)
    for key, p in patterns:
        for m in p.finditer(line):
            _try_apply_match(m, key, vals)
    return vals

def _line_to_match(line):
    if isinstance(line, bytes):
        line = line.decode()
    return line.rstrip()

def _try_apply_match(m, key, vals):
    groupdict = m.groupdict()
    if groupdict:
        return _try_apply_groupdict(groupdict, vals)
    groups = m.groups()
    len_groups = len(groups)
    if len_groups == 1:
        _try_apply_float(m.group(1), key, vals)
    elif len_groups == 2:
        _try_apply_float(m.group(2), m.group(1), vals)
    else:
        logging.warning(
            "bad unnamed group count %i for %r (expected 1 or 2) skipping",
            m.re.groups, m.re.pattern)

def _try_apply_groupdict(groupdict, vals):
    try:
        _try_apply_key_val_groupdict(groupdict, vals)
    except KeyError:
        for key, s in groupdict.items():
            _try_apply_float(s, key, vals)

def _try_apply_key_val_groupdict(groupdict, vals):
    key = groupdict["_key"]
    val = groupdict["_val"]
    _try_apply_float(val, key, vals)

def _try_apply_float(s, key, vals):
    try:
        f = float(s)
    except ValueError:
        pass
    else:
        vals[key] = f

class TestOutputLogger(object):

    @staticmethod
    def line(line):
        sys.stdout.write(line)
        sys.stdout.write("\n")

    def pattern_no_matches(self, pattern):
        sys.stdout.write(self._format_pattern_no_matches(pattern))
        sys.stdout.write("\n")

    @staticmethod
    def _format_pattern_no_matches(pattern):
        return "  %r: <no matches>" % pattern

    def pattern_matches(self, pattern, matches, vals):
        sys.stdout.write(self._format_pattern_matches(pattern, matches, vals))
        sys.stdout.write("\n")

    def _format_pattern_matches(self, pattern, matches, vals):
        groups = [m.groups() for m in matches]
        fmt_groups = self._strip_u(str(groups))
        fmt_vals = "(%s)" % ", ".join(
            ["%s=%s" % (name, val)
             for name, val in sorted(vals.items())])
        return "  %r: %s %s" % (pattern, fmt_groups, fmt_vals)

    @staticmethod
    def _strip_u(s):
        s = re.sub(r"u'(.*?)'", "'\\1'", s)
        s = re.sub(r"u\"(.*?)\"", "\"\\1\"", s)
        return s

def test_output(f, config, cb=None):
    cb = cb or TestOutputLogger()
    patterns = _init_patterns(config)
    for line in f:
        line = _line_to_match(line)
        cb.line(line)
        for key, p in patterns:
            matches = list(p.finditer(line))
            if not matches:
                cb.pattern_no_matches(p.pattern)
                continue
            vals = {}
            for m in matches:
                _try_apply_match(m, key, vals)
            cb.pattern_matches(p.pattern, matches, vals)
