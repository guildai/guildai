# Click Patch

Guild patches the click library for two modifications:

1. Fixes shell completion when short form options are combined.

2. Strips the 'extra' help text from the click-generated parameter
   help, which is used to present additional information about a
   parameter and is otherwise not controllable.

## Shell completion using combined short-form options

Shell completion modification is not tested here. To recreate the
behavior, execute these steps manually:

Run completion for tests:

    $ guild check -nt <TAB>

The list of tests should be presented as completions.

Disable the patching and try to show the tests:

    $ SKIP_PATCH_CLICK=1 guild check -nt <TAB>

The tests are not shown as completions.

## Stripped extra help text

We strip the 'extra' help text from parameter help as a matter of
aesthetics as we can provide explicit parameter information in the
help text that we provide.

With the patch:

    >>> run("guild tensorboard --help")  # doctest: +REPORT_UDIFF
    Usage: guild tensorboard [OPTIONS] [RUN...]
    ...
    Options:
      -h, --host HOST             Name of host interface to listen on.
      -p, --port PORT             Port to listen on.
      --include-batch             Include batch runs.
      --refresh-interval SECONDS  Refresh interval (defaults to 5 seconds).
    ...
    <exit 0>

Without the patch:

    >>> run("SKIP_PATCH_CLICK=1 guild tensorboard --help")  # doctest: +REPORT_UDIFF
    Usage: guild tensorboard [OPTIONS] [RUN...]
    ...
    Options:
      -h, --host HOST             Name of host interface to listen on.
      -p, --port PORT             Port to listen on.  [0<=x<=65535]
      --include-batch             Include batch runs.
      --refresh-interval SECONDS  Refresh interval (defaults to 5 seconds).
                                  [x>=1]
    ...
    <exit 0>
