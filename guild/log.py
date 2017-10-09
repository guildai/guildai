import logging
import logging.config

class ConsoleLogHandler(logging.StreamHandler):

    DEFAULT_FORMATS = {
        "_": "%(message)s",
        "DEBUG": "%(levelname)s: %(message)s",
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
        }
    })
