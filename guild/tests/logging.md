# Logging

    >>> import logging
    >>> import guild.log

Here's a function that logs various messages:

    >>> def log_sample_messages():
    ...   logging.debug("debug entry")
    ...   logging.info("info entry")
    ...   logging.warn("warning entry")
    ...   logging.error("error entry")

## Default settings

Let's initialize logging with the default settings:

    >>> guild.log.init_logging()

Debug is not logged by default:

    >>> log_capture = LogCapture()
    >>> with log_capture:
    ...   log_sample_messages()
    >>> log_capture.print_all()
    info entry
    warning entry
    error entry

## Enable debug

Let's reinit with debug enabled:

    >>> guild.log.init_logging(logging.DEBUG)
    >>> with log_capture:
    ...   log_sample_messages()
    >>> log_capture.print_all()
    DEBUG: debug entry
    info entry
    warning entry
    error entry

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
