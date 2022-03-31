# Deprecated option

For 0.7.1 through 0.8.0, Guild is transitioning filter options. The
tests below illustrate.

Test commands are run in a temporary Guild home location.

    >>> gh = mkdtemp()

    >>> def test(cmd):
    ...     run(cmd, guild_home=gh)

Deprecation warnings:

    >>> test("guild ls -o xxx")
    guild: option -o is deprecated and was removed in version 0.8 - use -Fo instead
    <exit 1>

    >>> test("guild ls -l xxx")
    guild: option -l is deprecated and was removed in version 0.8 - use -Fl instead
    <exit 1>

    >>> test("guild ls -U")
    guild: option -U is deprecated and was removed in version 0.8 - use '-Fl -' instead
    <exit 1>

    >>> test("guild ls --unlabeled")
    guild: option --unlabeled is deprecated and was removed in version 0.8 - use '--label -' instead
    <exit 1>

    >>> test("guild ls -M")
    guild: option -M is deprecated and was removed in version 0.8 - use -Fm instead
    <exit 1>

    >>> test("guild ls -N")
    guild: option -N is deprecated and was removed in version 0.8 - use -Fn instead
    <exit 1>

    >>> test("guild ls -D xxx")
    guild: option -D is deprecated and was removed in version 0.8 - use -Fd instead
    <exit 1>

    >>> test("guild ls -R")
    guild: option -R is deprecated and was removed in version 0.8 - use -Sr instead
    <exit 1>

    >>> test("guild ls -C")
    guild: option -C is deprecated and was removed in version 0.8 - use -Sc instead
    <exit 1>

    >>> test("guild ls -E")
    guild: option -E is deprecated and was removed in version 0.8 - use -Se instead
    <exit 1>

    >>> test("guild ls -T")
    guild: option -T is deprecated and was removed in version 0.8 - use -St instead
    <exit 1>

    >>> test("guild ls -P")
    guild: option -P is deprecated and was removed in version 0.8 - use -Sp instead
    <exit 1>

    >>> test("guild ls -G")
    guild: option -G is deprecated and was removed in version 0.8 - use -Sg instead
    <exit 1>
