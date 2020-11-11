# Test Flags

The `run` command supports a `--test-flags` option that prints
operation flag information.

## Printed Flag Attrs

The list of printed flag attrs for a test are defined by:

    >>> from guild.commands.run_impl import FLAG_TEST_ATTRS

This is the list of public flag attrs that are skipped:

    >>> SKIPPED = [
    ...   "name",
    ...   "opdef",
    ...   "extra",
    ...   "description",
    ... ]

Here's a default flag def:

    >>> from guild.guildfile import FlagDef

    >>> f = FlagDef("f", {}, None)

Verify that the `FLAG_TEST_ATTRS` covers all of the flag's public
attrs except those defined in `SKIPPED`.

    >>> public_attrs = [name for name in __builtins__["dir"](f) if name[0] != "_"]

Missed attrs:

    >>> missing = set(public_attrs) - set(SKIPPED) - set(FLAG_TEST_ATTRS)

    >>> len(missing), missing
    (0, ...)
