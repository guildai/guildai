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

import logging
import logging.config
import os
import sys

from guild import ansi_util  # lightweight

__last_init_kw = None

_isatty = sys.stderr.isatty()
_shell = os.getenv("SHELL")

NOISY_LOGGERS = (
    "chardet",
    "matplotlib",
)


class _FakeTTY:
    """Context manager for forcing _isatty to True - used for tests."""

    _saved = None

    def __enter__(self):
        self._saved = _isatty
        globals()["_isatty"] = True

    def __exit__(self, *_exc):
        assert self._saved is not None
        globals()["_isatty"] = self._saved


class _FakeShell:
    """Context manager for defining _shell as 'fake' - used for tests."""

    _saved = None

    def __enter__(self):
        self._saved = _shell
        globals()["_shell"] = "fake"

    def __exit__(self, *_exc):
        globals()["_shell"] = self._saved


class Formatter(logging.Formatter):
    def format(self, record):
        return self._maybe_strip_ansi(
            self._color(super().format(record), record.levelno)
        )

    @staticmethod
    def _color(s, level):
        if not _isatty or not _shell:
            return s
        if level >= logging.ERROR:
            return f"\033[31m{s}\033[0m"
        if level >= logging.WARNING:
            return f"\033[33m{s}\033[0m"
        return s

    @staticmethod
    def _maybe_strip_ansi(s):
        if _isatty:
            return s
        return ansi_util.strip_ansi_format(s)


class ConsoleLogHandler(logging.StreamHandler):
    DEFAULT_FORMATS = {
        "_": "%(levelname)s: %(message)s",
        "DEBUG": "%(levelname)s: [%(name)s] %(message)s",
        "INFO": "%(message)s",
    }

    def __init__(self, formats=None):
        super().__init__()
        formats = formats or self.DEFAULT_FORMATS
        self._formatters = {level: Formatter(fmt) for level, fmt in formats.items()}

    def format(self, record):
        fmt = self._formatters.get(record.levelname) or self._formatters.get("_")
        if fmt:
            return fmt.format(record)
        return super().format(record)


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
            "handlers": {
                "console": console_handler
            },
            "root": {
                "level": level,
                "handlers": ["console"]
            },
            "disable_existing_loggers": False,
        }
    )
    globals()["__last_init_kw"] = {"level": level, "formats": formats}


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
        import absl.logging as _unused
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
    if not _shell:
        return text
    return f"\x1b[2m{text}\x1b[0m"
