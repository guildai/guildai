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

    >>> guild.log.init_logging(**original_log_settings)

## Controlling log level with env var

The env var `LOG_LEVEL` can be used to configure Guild's log level.

To illustrate we can silence `INFO` level logs by setting `LOG_LEVEL`
to a value above 20.

The `resource-flags` project provides various operations that resolve
dependencies. Guild logs `INFO` level messages to let the user know
what's being resolved.

    >>> use_project("resource-flags")

    >>> run("guild run file-source -y")
    Resolving file:foo.txt
    <exit 0>

By setting `LOG_LEVEL` to 30 (the `WARN` level) we can squelch these
messages.

    >>> run("LOG_LEVEL=30 guild run file-source -y")
    <exit 0>
