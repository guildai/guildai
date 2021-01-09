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
import os
import re

import six
import yaml

from guild import util
from guild import yaml_util

log = logging.getLogger("guild")

ANONYMOUS_FUNCTION_P = re.compile(r"\[([^:]+:.+)\]")
NAMED_FUNCTION_P = re.compile(r"([a-zA-Z0-9_\-\.]+)\[(.*)\]")

LIST_CONCAT_P = re.compile(r"(\[.*\])\s*\*\s*([0-9]+)$")
SCIENTIFIC_NOTATION_RUN_ID_P = re.compile(r"[0-9]+e[0-9]+")
FUNCTION_ARG_DELIM = ":"
SEQUENCE_FLAG_FUNCTIONS = ("range", "linspace", "geomspace", "logspace")

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
    elif isinstance(val, dict):
        return _encode_dict(val)
    else:
        return yaml_util.encode_yaml(val, default_flow_style=True)


def _encode_list(val_list):
    joined = ", ".join([_encode_list_item(val) for val in val_list])
    return "[%s]" % joined


def _encode_list_item(val):
    encoded = encode_flag_val(val)
    if isinstance(val, six.string_types) and "," in encoded:
        return repr(encoded)
    return encoded


def _encode_dict(d):
    encoded_kv = [
        (encode_flag_val(k), encode_flag_val(v)) for k, v in sorted(d.items())
    ]
    return "{%s}" % ", ".join(["%s: %s" % kv for kv in encoded_kv])


def decode_flag_val(s, flag_type=None, nofix=False):
    decoded = _decode_flag_val(s, flag_type, nofix)
    if nofix:
        return decoded
    return _fix_surprising_number(decoded, s)


def _decode_flag_val(s, flag_type=None, nofix=False):
    if s == "":
        return s
    decoders = _flag_decoders_for_type(flag_type, nofix)
    for f, e_type in decoders:
        try:
            return f(s)
        except e_type:
            pass
        except Exception as e:
            log.warning("error decoding %r: %s", s, e)
    return s


def _flag_decoders_for_type(flag_type, nofix):
    return _base_decoders_for_type(flag_type) + _default_flag_decoders(nofix)


def _base_decoders_for_type(flag_type):
    """Return a list of base decoders for a flag type.

    With an explicit flag type, we can provide decoders applicable for
    the type without having to test decoding.
    """
    if flag_type in (None, "auto"):
        return []
    elif flag_type in ("string", "path", "existing-path"):
        return [(_string_type, ValueError)]
    elif flag_type == "int":
        return [(int, ValueError)]
    elif flag_type == "float":
        return [(float, ValueError)]
    elif flag_type == "number":
        return _number_decoders(True)
    elif flag_type == "boolean":
        return [(_boolean_type, (ValueError, yaml.YAMLError))]
    else:
        log.warning("uknown flag type %s, assuming 'auto'", flag_type)
        return []


def _string_type(s):
    # Special handling for strings that look like they're formatted as
    # YAML.
    if s[:1] in ("[", "'", "\"", "{"):
        raise ValueError()
    return six.text_type(s)


def _boolean_type(s):
    val = yaml_util.decode_yaml(s)
    if isinstance(val, (bool, int, float)):
        return bool(val)
    return val


def _default_flag_decoders(nofix):
    return _number_decoders(nofix) + [
        (_flag_function_or_expanded_sequence, ValueError),
        (_concatenated_list, ValueError),
        (_yaml_flag_decoder(nofix), (ValueError, yaml.YAMLError)),
    ]


def _number_decoders(nofix=False):
    if nofix:
        # Order matters - try int first as float succeeds with ints.
        return [(int, ValueError), (float, ValueError)]
    else:
        return [(int, ValueError)]


def _flag_function_or_expanded_sequence(s):
    """Returns a flag function spec or expanded function if applicable.

    If s can be decoded as a flag function it is returned as a string
    value to prevent it from being decoded by YAML, which can
    accidentally decode it as a list (see below for details).

    If s can be expanded to a sequence, the return value is a list
    containing the expanded items.

    Guild treats "[1:2]" as an anonymous flag function, which is
    passed along as a string to be decoded downstream. However, YAML
    treats "[1:2]" as a list containing a time value (one minute, two
    seconds), and therefore returns the value `[62]`. This function
    ensures that anonymous flag functions are returned as decoded
    string values. Provided this function is used prior to YAML
    decoding, the value is decoded correctly.

    Raises ValueError if s is not a special flag function.

    Raises TypeError if the arguments provided to flag function are
    invalid.
    """
    name, args = decode_flag_function(s)
    if _is_anonymous_flag_function(name, args):
        return s
    elif _is_sequence_flag_function(name):
        return _expand_sequence(name, args)
    else:
        raise ValueError(s)


def _is_anonymous_flag_function(name, args):
    return name is None and len(args) >= 2


def _is_sequence_flag_function(name):
    return name in SEQUENCE_FLAG_FUNCTIONS


def _expand_sequence(name, args):
    f = globals().get("_expand_%s" % name)
    assert f, name
    return f(*args)


def _expand_range(*args):
    import numpy as np

    start, end, step = _expand_range_args(*args)
    return [_np_seq_val(x) for x in np.arange(start, end, step)]


def _expand_range_args(start=None, end=None, step=1, *rest):
    if rest:
        log.warning("unsupported arguments for range function: %s - ignoring", rest)
    _assert_required_function_args(start)
    _assert_numeric_function_args(start, step)
    if end is not None:
        _assert_numeric_function_args(end)
        end = end + min(step, 1)
    return start, end, step


def _assert_required_function_args(*args):
    for arg in args:
        if arg is None:
            raise TypeError("function requires at least %i arg(s)" % len(args))


def _assert_numeric_function_args(*args):
    for arg in args:
        if not isinstance(arg, (int, float)):
            raise TypeError("invalid arg %r: expected a number" % arg)


def _np_seq_val(x):
    x = x.item()
    if isinstance(x, float) and x > 1e-8:
        return round(x, 8)
    return x


def _expand_linspace(*args):
    import numpy as np

    start, end, count = _expand_linspace_args(*args)
    return [_np_seq_val(x) for x in np.linspace(start, end, count)]


def _expand_linspace_args(start=None, end=None, count=5, *rest):
    if rest:
        log.warning("unsupported arguments for linspace function: %s - ignoring", rest)
    _assert_required_function_args(start, end)
    _assert_numeric_function_args(start, end, count)
    return start, end, count


def _expand_logspace(*args):
    import numpy as np

    start, end, count, base = _expand_logspace_args(*args)
    return [_np_seq_val(x) for x in np.logspace(start, end, count, base=base)]


def _expand_logspace_args(start=None, end=None, count=5, base=10, *rest):
    if rest:
        log.warning("unsupported arguments for logspace function: %s - ignoring", rest)
    _assert_required_function_args(start, end)
    _assert_numeric_function_args(start, end, count, base)
    return start, end, count, base


def _anonymous_flag_function(s):
    """Returns s as a string if s is an anonymous flag function.

    An anonymous flag function is in the form `[N:M...]`. This
    function can be applied before attempt a conversion to YAML to
    avoid accidentally converting time values to integers. E.g. YAML
    decodes the string "1:1" as a time value of 1 minute + 1 second
    and returns an integer of 61. The value "[1:1]", which Guild
    treats an anonymous flag function, is therefore decoded as a list
    containing a single integer of 61.
    """
    name, args = decode_flag_function(s)
    if name is None and len(args) >= 2:
        return s
    raise ValueError(s)


def _concatenated_list(s):
    """Expands list concatantion syntax to a list of repeating values.

    For example, the value "[1]*3" is expanded to `[1,1,1]`, the value
    "[1,2]*2" to `[1,2,1,2]` and so on.
    """
    m = LIST_CONCAT_P.match(s.strip())
    if not m:
        raise ValueError(s)
    maybe_list = _decode_flag_val(m.group(1))
    if isinstance(maybe_list, list):
        return maybe_list * int(m.group(2))
    return s


def _yaml_flag_decoder(nofix):
    if nofix:
        return yaml_util.decode_yaml
    else:
        return _decode_yaml_with_fix


def _decode_yaml_with_fix(s):
    """Skips yaml decode if s looks like a run ID."""
    if _is_scientific_notation_run_id(s):
        return s
    return yaml_util.decode_yaml(s)


def _is_scientific_notation_run_id(s):
    return 3 <= len(s) <= 32 and SCIENTIFIC_NOTATION_RUN_ID_P.match(s)


def _fix_surprising_number(val, s):
    """Returns s in cases where val is a surprising result."""
    if (
        isinstance(val, (int, float))
        and "!!" not in s
        and _contains_non_numeric_chars(s)
    ):
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
    name, args_raw = _split_flag_function(s)
    args_encoded = args_raw.split(FUNCTION_ARG_DELIM) if args_raw else []
    args = [decode_flag_val(encoded.strip(), nofix=True) for encoded in args_encoded]
    return name, tuple(args)


def _split_flag_function(s):
    result = util.find_apply([_split_named_function, _split_anonymous_function], s)
    if result is None:
        raise ValueError("not a function")
    return result


def _split_named_function(s):
    m = NAMED_FUNCTION_P.match(s)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def _split_anonymous_function(s):
    # Regex is not sufficient to handle differences between anonymous
    # functions and YAML encoded lists. We perform a sniff test to see
    # if it might be an anonymous function and then confirm by
    # decoding it as YAML and testing the result.
    if s[:1] == "[" and s[-1:] == "]" and ":" in s:
        try:
            l = yaml_util.decode_yaml(s)
        except Exception:
            return None, s[1:-1]
        else:
            if len(l) == 1 and isinstance(l[0], (six.string_types, int)):
                return None, s[1:-1]
    return None


def is_flag_function(val):
    if not isinstance(val, six.string_types):
        return False
    try:
        _split_flag_function(val)
    except ValueError:
        return False
    else:
        return True


def flag_assigns(flags, truncate_floats=False, shorten_paths=False):
    """Returns a list of formatted flags for a map of flags.

    Formatted flags are sorted by flag name and have the form
    NAME=FORMATTED_VALUE.
    """
    return [
        flag_assign(name, val, truncate_floats, shorten_paths)
        for name, val in sorted(flags.items())
    ]


def flag_assign(name, val, truncate_floats=False, shorten_paths=False):
    return "%s=%s" % (name, format_flag(val, truncate_floats, shorten_paths))


def format_flag(val, truncate_floats=False, shorten_paths=False):
    encoded = encode_flag_val(val)
    if truncate_floats and isinstance(val, float):
        trunc_len = _trunc_len(truncate_floats)
        encoded = _truncate_formatted_float(encoded, trunc_len)
    if shorten_paths and _is_path(val):
        path_len = _path_len(shorten_paths)
        encoded = util.shorten_path(val, path_len)
    return _quote_encoded(encoded, val)


def _trunc_len(truncate_floats):
    if truncate_floats is True:
        return DEFAULT_FLOAT_TRUNC_LEN
    if not isinstance(truncate_floats, int):
        raise ValueError(
            "invalid value for truncate_floats: %r (expected int)" % truncate_floats
        )
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
            "invalid value for shorten_paths: %r (expected int)" % shorten_paths
        )
    return shorten_paths


def _quote_encoded(encoded, val):
    if _needs_quote(encoded, val):
        return _quote(encoded)
    return encoded


def _needs_quote(encoded, val):
    return (
        isinstance(val, six.string_types)
        and encoded[0] not in ("'", "\"")
        and " " in encoded
    )


def _quote(s):
    return repr(s)


def _truncate_formatted_float(s, trunc_len):
    parts = re.split(r"(\.[0-9]+)", s)
    return "".join([_maybe_truncate_dec_part(part, trunc_len) for part in parts])


def _maybe_truncate_dec_part(part, trunc_len):
    if part[:1] != ".":
        return part
    if len(part) <= trunc_len:  # lte to include leading '.'
        return part
    return part[: trunc_len + 1]


def split_encoded_flag_val(encoded, split_spec):
    if split_spec is True or split_spec == "shlex":
        return util.shlex_split(encoded)
    else:
        return _string_split(encoded, split_spec)


def _string_split(encoded, sep):
    return [part for part in encoded.split(str(sep)) if part]


def join_splittable_flag_vals(vals, split_spec):
    encoded_vals = [encode_flag_val(val) for val in vals]
    if split_spec in (None, True, "shlex"):
        return " ".join([util.shlex_quote(x) for x in encoded_vals])
    elif isinstance(split_spec, six.string_types):
        return split_spec.join(encoded_vals)
    else:
        raise ValueError("split_spec must be None, True, or a string: %r" % split_spec)
