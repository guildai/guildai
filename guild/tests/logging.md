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
    ...   test_logger.warn("warning entry")
    ...   test_logger.error("error entry")

## Initializing logging

We use the `init_loggin` function to initialize the logging
facility. First, let's save the current settings so we can restore
them at the end of our tests.

    >>> original_log_settings = guild.log.current_settings()

Let's initialize logging with the default settings:

    >>> guild.log.init_logging()

Debug is not logged by default:

    >>> log_capture = LogCapture()
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
