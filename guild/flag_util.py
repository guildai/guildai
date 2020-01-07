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

import os
import re
import yaml

import six

from guild import util

FUNCTION_P = re.compile(r"([a-zA-Z0-9_\-\.]*)\[(.*)\]\s*$")
LIST_CONCAT_P = re.compile(r"(\[.*\])\s*\*\s*([0-9]+)$")
SCIENTIFIC_NOTATION_RUN_ID_P = re.compile(r"[0-9]+e[0-9]+")
FUNCTION_ARG_DELIM = ":"

DEFAULT_FLOAT_TRUNC_LEN = 5
DEFAULT_SHORTENED_PATH_LEN = 20

def encode_flag_val(val):
    if val is True:
        return "yes"
    elif val is False:
        return "no"
    elif val is None:
        return "null"
    elif isinstance(val, list):
        return _encode_list(val)
    elif isinstance(val, float):
        return _yaml_encode(val)
    elif isinstance(val, six.string_types):
        return _encode_str(val)
    elif isinstance(val, dict):
        return _encode_dict(val)
    else:
        return str(val)

def _encode_list(val_list):
    joined = ", ".join([encode_flag_val(val) for val in val_list])
    return "[%s]" % joined

def _yaml_encode(val):
    return _strip_yaml(yaml.safe_dump(val).strip())

def _strip_yaml(s):
    if s.endswith("\n..."):
        return s[:-4]
    return s

def _encode_str(s):
    return _quote_float(_yaml_encode(s))

def _encode_dict(d):
    encoded_kv = [
        (encode_flag_val(k), encode_flag_val(v))
        for k, v in sorted(d.items())]
    return "{%s}" % ", ".join(["%s: %s" % kv for kv in encoded_kv])

def _quote_float(s):
    """Returns s quoted if s can be coverted to a float."""
    try:
        float(s)
    except ValueError:
        return s
    else:
        return "'%s'" % s

def decode_flag_val(s):
    return _fix_surprising_number(_decode_flag_val(s), s)

def _decode_flag_val(s):
    if s == "":
        return s
    decoders = [
        (int, ValueError),
        (_anonymous_flag_function, ValueError),
        (_concatenated_list, ValueError),
        (_yaml_parse, (ValueError, yaml.YAMLError)),
    ]
    for f, e_type in decoders:
        try:
            return f(s)
        except e_type:
            pass
    return s

def _concatenated_list(s):
    m = LIST_CONCAT_P.match(s.strip())
    if not m:
        raise ValueError(s)
    maybe_list = _decode_flag_val(m.group(1))
    if isinstance(maybe_list, list):
        return maybe_list * int(m.group(2))
    return s

def _anonymous_flag_function(s):
    name, args = decode_flag_function(s)
    if name is None and len(args) >= 2:
        return s
    raise ValueError(s)

def _yaml_parse(s):
    if _is_scientific_notation_run_id(s):
        return s
    return yaml.safe_load(s)

def _is_scientific_notation_run_id(s):
    return 3 <= len(s) <= 8 and SCIENTIFIC_NOTATION_RUN_ID_P.match(s)

def _fix_surprising_number(val, s):
    """Returns s in cases where val is a surprising result."""
    if (isinstance(val, (int, float)) and
        "!!" not in s and
        _contains_non_numeric_chars(s)):
        return s
    return val

def _contains_non_numeric_chars(s):
    for char in s:
        if char in ("_", ":"):
            return True
    return False

def decode_flag_function(s):
    if not isinstance(s, six.string_types):
        raise ValueError("requires string")
    m = FUNCTION_P.match(s)
    if not m:
        raise ValueError("not a function")
    name = m.group(1) or None
    args_raw = m.group(2).strip()
    if args_raw:
        args_s = args_raw.split(FUNCTION_ARG_DELIM)
    else:
        args_s = []
    args = [decode_flag_val(arg.strip()) for arg in args_s]
    return name, tuple(args)

def is_flag_function(val):
    if not isinstance(val, six.string_types):
        return False
    try:
        decode_flag_function(val)
    except ValueError:
        return False
    else:
        return True

def format_flags(flags, truncate_floats=False, shorten_paths=False):
    return [
        _flag_assign(name, val, truncate_floats, shorten_paths)
        for name, val in sorted(flags.items())]

def _flag_assign(name, val, truncate_floats, shorten_paths):
    return "%s=%s" % (name, format_flag(val, truncate_floats, shorten_paths))

def format_flag(val, truncate_floats=False, shorten_paths=False):
    fmt_val = encode_flag_val(val)
    if truncate_floats and isinstance(val, float):
        trunc_len = _trunc_len(truncate_floats)
        fmt_val = _truncate_formatted_float(fmt_val, trunc_len)
    if shorten_paths and _is_path(val):
        path_len = _path_len(shorten_paths)
        fmt_val = util.shorten_path(val, path_len)
    return _quote_encoded(fmt_val, val)

def _trunc_len(truncate_floats):
    if truncate_floats is True:
        return DEFAULT_FLOAT_TRUNC_LEN
    if not isinstance(truncate_floats, int):
        raise ValueError(
            "invalid value for truncate_floats: %r (expected int)"
            % truncate_floats)
    return truncate_floats

def _is_path(val):
    return (
        isinstance(val, six.string_types) and os.path.sep in val and os.path.exists(val)
    )

def _path_len(shorten_paths):
    if shorten_paths is True:
        return DEFAULT_SHORTENED_PATH_LEN
    if not isinstance(shorten_paths, int):
        raise ValueError(
            "invalid value for shorten_paths: %r (expected int)"
            % shorten_paths)
    return shorten_paths

def _quote_encoded(encoded, val):
    if _needs_quote(encoded, val):
        return _quote(encoded)
    return encoded

def _needs_quote(encoded, val):
    return (
        isinstance(val, six.string_types) and
        " " in encoded and
        encoded[0] not in ("'", "\""))

def _quote(s):
    return repr(s)

def _truncate_formatted_float(s, trunc_len):
    parts = re.split(r"(\.[0-9]+)", s)
    return "".join([
        _maybe_truncate_dec_part(part, trunc_len)
        for part in parts])

def _maybe_truncate_dec_part(part, trunc_len):
    if part[:1] != ".":
        return part
    if len(part) <= trunc_len: # lte to include leading '.'
        return part
    return part[:trunc_len + 1]

class FormattedValue(object):

    _str = None

    def __init__(self, value, truncate_floats=False):
        self._truncate_floats = truncate_floats
        self._value = value

    @property
    def wrapped_value(self):
        return self._value

    @wrapped_value.setter
    def wrapped_value(self, value):
        self._value = value
        self._str = None

    def __str__(self):
        if self._str is None:
            self._str = format_flag(self._value, self._truncate_floats)
        return self._str

def _patch_yaml_safe_loader():
    """Patch yaml parsing to support Guild specific resolution rules.

    - Support scientific notation that does not contain periods
    - Special treatment for short form run IDs that are valid
      scientific notation

    """
    loader = yaml.SafeLoader
    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(u'''^(?:
        [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
        |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
        |\\.[0-9_]+(?:[eE][-+][0-9]+)?
        |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
        |[-+]?\\.(?:inf|Inf|INF)
        |\\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

_patch_yaml_safe_loader()
