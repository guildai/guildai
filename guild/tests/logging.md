# Logging

Logging in Guild is performed using Python's built in `logging` module
and related facility.

    >>> import logging

The module `guild.log` is used to initialize this facility.

    >>> import guild.log

For our tests, we'll create a function that logs various messages
using a logger named `test`.

Here's our test logger:

    >>> test_logger = logging.getLogger("test")

and our logging function:

    >>> def log_sample_messages():
    ...   test_logger.debug("debug entry")
    ...   test_logger.info("info entry")
    ...   test_logger.warning("warning entry")
    ...   test_logger.error("error entry")

## Initializing logging

We use the `init_logging` function to initialize the logging
facility. First, let's save the current settings so we can restore
them at the end of our tests.

    >>> original_log_settings = guild.log.current_settings()

Let's initialize logging with the default settings:

    >>> guild.log.init_logging()

Debug is not logged by default:

    >>> log_capture = LogCapture(use_root_handler=True)
    >>> with log_capture:
    ...   log_sample_messages()
    >>> log_capture.print_all()
    info entry
    WARNING: warning entry
    ERROR: error entry

## Enable debug

Let's reinit with debug enabled:

    >>> guild.log.init_logging(logging.DEBUG)
    >>> with log_capture:
    ...   log_sample_messages()
    >>> log_capture.print_all()
    DEBUG: [test] debug entry
    info entry
    WARNING: warning entry
    ERROR: error entry

## Color

If a TTY is available and the SHELL environment variable is defined,
output is colored. Warnings are displayed in yellow (color code 33)
and errors in red (color code 31).

    >>> with guild.log._FakeTTY():
    ...   with guild.log._FakeShell():
    ...      with LogCapture(use_root_handler=True, strip_ansi_format=False) as tty_logs:
    ...          log_sample_messages()
    ...      tty_logs.print_all() # doctest: -STRIP_ANSI_FMT
    DEBUG: [test] debug entry
    info entry
    [33mWARNING: warning entry[0m
    [31mERROR: error entry[0m

## Custom formats

Let's specify some custom level formats:

    >>> guild.log.init_logging(
    ...   logging.DEBUG,
    ...   formats={"_": "%(levelno)i %(message)s"})
    >>> with log_capture:
    ...   log_sample_messages()
    >>> log_capture.print_all()
    10 debug entry
    20 info entry
    30 warning entry
    40 error entry

Here we'll define the WARN and ERROR formats:

    >>> guild.log.init_logging(
    ...   logging.DEBUG,
    ...   formats={"WARNING": "!! %(message)s",
    ...            "ERROR": "!!! %(message)s"})
    >>> with log_capture:
    ...   log_sample_messages()
    >>> log_capture.print_all()
    debug entry
    info entry
    !! warning entry
    !!! error entry

## Restoring logging

We need to restore logging to its defaults:

    >>> guild.log.init_logging(**original_log_settings)  # doctest: -PYTEST_ONLY
