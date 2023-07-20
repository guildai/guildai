# Output Attrs

## Default output attrs

The default regular expression pattern Guild uses for output
attributes is defined in `guild.summary.DEFAULT_OUTPUT_ATTRS`.

    >>> from guild import summary

    >>> summary.DEFAULT_OUTPUT_ATTRS
    ['^(\\key):\\s+(\\value)$']

This pattern uses the `key` alias, which needs to be applied before
evaluating output lines.

    >>> p = summary.replace_aliases(
    ...     summary.DEFAULT_OUTPUT_ATTRS[0],
    ...     summary.OUTPUT_ATTR_ALIASES
    ... )
    >>> p = re.compile(p)

Apply to various patterns.

    >>> def test_p(val):
    ...     m = p.match(val)
    ...     if m:
    ...         print(m.groups())
    ...     else:
    ...         print("<no match>")

    >>> test_p("model: cnn")
    ('model', 'cnn')

    >>> test_p("custom-attr: red-green-blue")
    ('custom-attr', 'red-green-blue')

    >>> test_p("X: yz")
    ('X', 'yz')

Keys must start with a letter or an underscore.

    >>> test_p("1a123: hello")
    <no match>

    >>> test_p("a123: hello")
    ('a123', 'hello')

    >>> test_p("_a123: hello")
    ('_a123', 'hello')

The default pattern does not match keys with spaces. This is to avoid
unintentional matches with common output.

    >>> test_p("WARNING: Invalid intput")
    <no match>

However, Guild will capture output like this:

    >>> test_p("WARNING: Invalid!")
    ('WARNING', 'Invalid!')

In such cases, a user should configure output attributes explicitly.

## Sample projects
