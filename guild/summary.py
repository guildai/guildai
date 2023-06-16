# Copyright 2017-2023 Posit Software, PBC
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

import io
import logging
import re
import sys

from guild import tensorboard_util
from guild import util

log = logging.getLogger("guild")

ALIASES = [
    (re.compile(r"\\key"), "[^ \t]+"),
    (
        re.compile(r"\\value"),
        r"(?:[-+]?[0-9]*\.?(?:[0-9]+)?(?:[eE][-+]?[0-9]+)?"  #
        r"|[nN][aA][nN]"  #
        r"|[-+]?[iI][nN][fF])"
    ),
    (re.compile(r"\\step"), "[0-9]+"),
]

DEFAULT_OUTPUT_SCALARS = [
    r"\key: +\value\s+\((?:step\s+)?(?P<step>\step)\)$",
    r"^(\key):\s+(\value)(?:\s+\(.*\))?$",
]

HPARAM_TYPE_NUMBER = "number"
HPARAM_TYPE_BOOL = "bool"
HPARAM_TYPE_STRING = "string"
HPARAM_TYPE_NONE = "none"


class EventFileWriter:
    def __init__(
        self,
        logdir,
        max_queue_size=10,
        flush_secs=120,
        filename_base=None,
        filename_suffix="",
    ):
        util.ensure_dir(logdir)
        self._writer = tensorboard_util.AsyncWriter(
            logdir,
            max_queue_size=max_queue_size,
            flush_secs=flush_secs,
            filename_base=filename_base,
            filename_suffix=filename_suffix,
        )
        self.add_event(tensorboard_util.Event(file_version="brain.Event:2"))
        self.flush()

    def add_event(self, event):
        self._writer.write(event.SerializeToString())

    def flush(self):
        self._writer.flush()

    def close(self):
        self._writer.close()


class _HParamState:
    def __init__(self):
        self._numeric = set()
        self._discrete = {}

    def add_numeric(self, name):
        self._numeric.add(name)

    def add_discrete(self, name, vals):
        self._discrete[name] = vals


class SummaryWriter:
    def __init__(self, logdir, filename_base=None, filename_suffix=""):
        self.logdir = logdir
        self._writer_init = lambda: EventFileWriter(
            logdir, filename_base=filename_base, filename_suffix=filename_suffix
        )
        self._writer = None

    def _get_writer(self):
        if self._writer is None:
            self._writer = self._writer_init()
        return self._writer

    def _add_summary(self, summary, step=None):
        if step is not None:
            step = int(step)
        event = tensorboard_util.Event(summary=summary, step=step)
        self._get_writer().add_event(event)

    def add_scalar(self, tag, val, step=None):
        self._add_summary(_ScalarSummary(tag, val), step)

    def add_image(self, tag, image):
        from PIL import Image

        image = Image.open(image)
        encoded = _try_encode_png(image)
        if encoded:
            summary = _ImageSummary(
                tag, image.height, image.width, len(image.getbands()), encoded
            )
            self._add_summary(summary)

    def add_hparam_experiment(self, hparams, metrics):
        self._add_summary(_HParamExperiment(hparams, metrics))

    def add_hparam_session(self, name, hparams, status=None):
        self._add_summary(_HParamSessionStart(name, hparams))
        if status:
            self._add_summary(_HParamSessionEnd(status))

    def flush(self):
        if self._writer:
            self._writer.flush()

    def close(self):
        if self._writer:
            self._writer.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def _ScalarSummary(tag, val):
    return tensorboard_util.Summary(tag, simple_value=val)


def _ImageSummary(tag, height, width, colorspace, encoded_image):
    image = tensorboard_util.Image(
        height=height,
        width=width,
        colorspace=colorspace,
        encoded_image_string=encoded_image,
    )
    return tensorboard_util.Summary(tag, image=image)


def _try_encode_png(image):
    bytes = io.BytesIO()
    try:
        image.save(bytes, format='PNG')
    except Exception as e:
        image_desc = _image_desc(image)
        log.error("error encoding %s: %s", image_desc, e)
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("encoding %s", image_desc)
        return None
    else:
        return bytes.getvalue()


def _image_desc(img):
    return getattr(getattr(img, "fp", None), "name", str(img))


def _HParamExperiment(hparams, metrics):
    hp = tensorboard_util.hparams_hp_proto()
    return hp.hparams_config_pb(
        hparams=[_HParam(key, vals) for key, vals in sorted(hparams.items())],
        metrics=[hp.Metric(tag) for tag in sorted(metrics)],
    )


def _HParam(name, vals):
    """Returns an `HParam` object for flag name and known values.

    Uses real interval domain iff all values are numeric.

    Uses discrete interval iff all values are strings.

    Otherwise does not use a domain.
    """
    hp = tensorboard_util.hparams_hp_proto()

    type = hparam_type(vals)
    if type == HPARAM_TYPE_NUMBER:
        return hp.HParam(name, hp.RealInterval(float("-inf"), float("inf")))
    if type == HPARAM_TYPE_BOOL:
        return hp.HParam(name, hp.Discrete((True, False)))
    if type == HPARAM_TYPE_STRING:
        return hp.HParam(name, hp.Discrete(vals))
    if type == HPARAM_TYPE_NONE:
        return hp.HParam(name)
    assert False, type


def hparam_type(vals):
    types = {_hparam_val_type(val) for val in vals}
    if len(types) == 1:
        return types.pop()
    return HPARAM_TYPE_NONE


def _hparam_val_type(val):
    if isinstance(val, str):
        return HPARAM_TYPE_STRING
    if type(val) in (float, int):
        return HPARAM_TYPE_NUMBER
    if val is True or val is False:
        return HPARAM_TYPE_BOOL
    return HPARAM_TYPE_NONE


def is_hparam_numeric(vals):
    # Avoid isinstance to check for numeric as booleans extend int.
    # pylint: disable=unidiomatic-typecheck
    return all((type(val) in (int, float) for val in vals))


def is_hparam_boolean(vals):
    return all((val in (True, False) for val in vals))


def is_hparam_string(vals):
    return all((isinstance(val, str) for val in vals))


def _HParamSessionStart(name, hparams):
    hp = tensorboard_util.hparams_hp_proto()
    try:
        # pylint: disable=unexpected-keyword-arg
        return hp.hparams_pb(hparams, trial_id=name)
    except TypeError:
        return _legacy_hparams_pb(hparams, name)


def _legacy_hparams_pb(hparams, trial_id):
    hp = tensorboard_util.hparams_hp_proto()
    hparams = hp._normalize_hparams(hparams)
    info = hp.plugin_data_pb2.SessionStartInfo(group_name=trial_id)
    for name in sorted(hparams):
        val = hparams[name]
        if isinstance(val, bool):
            info.hparams[name].bool_value = val
        elif isinstance(val, (float, int)):
            info.hparams[name].number_value = val
        elif isinstance(val, str):
            info.hparams[name].string_value = val
        elif val is None:
            info.hparams[name].string_value = ""
        else:
            info.hparams[name].string_value = str(val)
    return hp._summary_pb(
        hp.metadata.SESSION_START_INFO_TAG,
        hp.plugin_data_pb2.HParamsPluginData(session_start_info=info),
    )


def _HParamSessionEnd(status):
    hp = tensorboard_util.hparams_hp_proto()
    info = hp.plugin_data_pb2.SessionEndInfo(status=_Status(status))
    return hp._summary_pb(
        hp.metadata.SESSION_END_INFO_TAG,
        hp.plugin_data_pb2.HParamsPluginData(session_end_info=info),
    )


def _Status(status):
    api = tensorboard_util.hparams_api_proto()
    if status in ("terminated", "completed"):
        return api.Status.Value("STATUS_SUCCESS")
    if status == "error":
        return api.Status.Value("STATUS_FAILURE")
    if status == "running":
        return api.Status.Value("STATUS_RUNNING")
    return api.Status.Value("STATUS_UNKNOWN")


class OutputScalars:
    def __init__(self, config, output_dir, ignore=None):
        self._patterns = _init_patterns(config)
        self._writer = SummaryWriter(output_dir)
        self._ignore = set(ignore or [])
        self._step = None

    def write(self, line):
        vals = _match_line(line, self._patterns)
        step = vals.pop("step", None)
        if step is not None:
            self._step = step
        if vals:
            for key, val in sorted(vals.items()):
                log.debug("scalar %s val=%s step=%s", key, val, self._step)
                if key in self._ignore:
                    log.debug("skipping %s because it's in ignore list", key)
                    continue
                self._writer.add_scalar(key, val, self._step)
                self._writer.flush()

    def close(self):
        self._writer.close()

    def flush(self):
        self._writer.flush()

    def print_patterns(self):
        for key, p in self._patterns:
            sys.stdout.write(f"{key}: {p.pattern}\n")


def _init_patterns(config):
    if not isinstance(config, list):
        raise TypeError(f"invalid output scalar config: {config!r}")
    patterns = []
    for item in config:
        patterns.extend(_config_item_patterns(item))
    return patterns


def _config_item_patterns(item):
    if isinstance(item, dict):
        return _map_patterns(item)
    if isinstance(item, str):
        return _string_patterns(item)
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
    if not isinstance(val, str):
        log.warning("invalid output scalar pattern: %r", val)
        return []
    val = _replace_aliases(val)
    try:
        p = re.compile(val)
    except Exception as e:
        log.warning("error compiling pattern %s: %s", val, e)
        return []
    else:
        return [(key, p)]


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
        line = line.decode(errors="ignore")
    return line.rstrip()


def _try_apply_match(m, key, vals):
    groupdict = m.groupdict()
    if groupdict:
        _try_apply_groupdict(groupdict, vals)
        return
    groups = m.groups()
    len_groups = len(groups)
    if len_groups == 1:
        _try_apply_float(m.group(1), key, vals)
    elif len_groups == 2:
        _try_apply_float(m.group(2), m.group(1), vals)
    else:
        logging.warning(
            "bad unnamed group count %i for %r (expected 1 or 2) skipping",
            m.re.groups,
            m.re.pattern,
        )


def _try_apply_groupdict(groupdict, vals):
    try:
        key = groupdict["_key"]
        val = groupdict["_val"]
    except KeyError:
        for key, s in groupdict.items():
            _try_apply_float(s, key, vals)
    else:
        _try_apply_float(val, key, vals)


def _try_apply_float(s, key, vals):
    try:
        f = float(s)
    except (TypeError, ValueError):
        pass
    else:
        vals[key] = f


class TestOutputLogger:
    @staticmethod
    def line(line):
        sys.stdout.write(line)
        sys.stdout.write("\n")

    def pattern_no_matches(self, pattern):
        sys.stdout.write(self._format_pattern_no_matches(pattern))
        sys.stdout.write("\n")

    @staticmethod
    def _format_pattern_no_matches(pattern):
        return f"  {pattern!r}: <no matches>"

    def pattern_matches(self, pattern, matches, vals):
        sys.stdout.write(self._format_pattern_matches(pattern, matches, vals))
        sys.stdout.write("\n")

    def _format_pattern_matches(self, pattern, matches, vals):
        groups = _strip_u(str([m.groups() for m in matches]))
        assigns = ", ".join([f"{name}={val}" for name, val in sorted(vals.items())])
        return f"  {pattern!r}: {groups} ({assigns})"


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
