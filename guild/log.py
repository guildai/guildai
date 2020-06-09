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
import logging.config
import os
import sys

__last_init_kw = None

_isatty = sys.stderr.isatty()

NOISY_LOGGERS = (
    "chardet",
    "matplotlib",
)


class _FakeTTY(object):
    """Context manager for forcing _isatty to True - used for tests."""

    _saved = None

    def __enter__(self):
        self._saved = _isatty
        globals()["_isatty"] = True

    def __exit__(self, *_exc):
        assert self._saved is not None
        globals()["_isatty"] = self._saved


class Formatter(logging.Formatter):
    def format(self, record):
        return self._color(super(Formatter, self).format(record), record.levelno)

    @staticmethod
    def _color(s, level):
        if not _isatty:
            return s
        if level >= logging.ERROR:
            return "\033[31m%s\033[0m" % s
        elif level >= logging.WARNING:
            return "\033[33m%s\033[0m" % s
        else:
            return s


class ConsoleLogHandler(logging.StreamHandler):

    DEFAULT_FORMATS = {
        "_": "%(levelname)s: %(message)s",
        "DEBUG": "%(levelname)s: [%(name)s] %(message)s",
        "INFO": "%(message)s",
    }

    def __init__(self, formats=None):
        super(ConsoleLogHandler, self).__init__()
        formats = formats or self.DEFAULT_FORMATS
        self._formatters = {level: Formatter(fmt) for level, fmt in formats.items()}

    def format(self, record):
        fmt = self._formatters.get(record.levelname) or self._formatters.get("_")
        if fmt:
            return fmt.format(record)
        else:
            return super(ConsoleLogHandler, self).format(record)


def init_logging(level=None, formats=None):
    level = _log_level_for_arg(level)
    _preempt_logging_mods()
    console_handler = {
        "class": "guild.log.ConsoleLogHandler",
        "formats": formats,
    }
    logging.config.dictConfig(
        {
            "version": 1,
            "handlers": {"console": console_handler},
            "root": {"level": level, "handlers": ["console"]},
            "disable_existing_loggers": False,
        }
    )
    globals()["__last_init_kw"] = dict(level=level, formats=formats)


def _log_level_for_arg(arg):
    if arg is not None:
        return arg
    try:
        return int(os.environ["LOG_LEVEL"])
    except (KeyError, TypeError):
        return logging.INFO


def _preempt_logging_mods():
    """Preempt known logging mods.

    Some modules modify logging without respecting previous config
    (e.g. absl.logging). This function preempts those changes so that
    our config is applied afterward.
    """
    try:
        import absl.logging as _
    except Exception:
        pass


def disable_noisy_loggers(level=logging.INFO):
    if level <= logging.DEBUG:
        _set_logger_level(NOISY_LOGGERS, logging.INFO)


def _set_logger_level(pkgs, level):
    for pkg in pkgs:
        log = logging.getLogger(pkg)
        log.setLevel(level)


def current_settings():
    return __last_init_kw


def dim(text):
    return "\x1b[2m%s\x1b[0m" % text
