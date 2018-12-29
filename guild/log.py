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

import logging
import logging.config

__last_init_kw = None

class ConsoleLogHandler(logging.StreamHandler):

    DEFAULT_FORMATS = {
        "_": "%(levelname)s: %(message)s",
        "DEBUG": "%(levelname)s: [%(name)s] %(message)s",
        "INFO": "%(message)s",
    }

    def __init__(self, formats=None):
        super(ConsoleLogHandler, self).__init__()
        formats = formats or self.DEFAULT_FORMATS
        self._formatters = {
            level: logging.Formatter(fmt)
            for level, fmt in formats.items()
        }

    def format(self, record):
        fmt = (self._formatters.get(record.levelname) or
               self._formatters.get("_"))
        if fmt:
            return fmt.format(record)
        else:
            return super(ConsoleLogHandler, self).format(record)

def init_logging(level=logging.INFO, formats=None):
    console_handler = {
        "class": "guild.log.ConsoleLogHandler",
        "formats": formats,
    }
    logging.config.dictConfig({
        "version": 1,
        "handlers": {
            "console": console_handler
        },
        "root": {
            "level": level,
            "handlers": ["console"]
        },
        "disable_existing_loggers": False,
    })
    globals()["__last_init_kw"] = dict(level=level, formats=formats)

def current_settings():
    return __last_init_kw
