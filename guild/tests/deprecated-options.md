# Deprecated option

For 0.7.1 through 0.8.0, Guild is transitioning filter options. The
tests below illustrate.

Test commands are run in a temporary Guild home location.

    >>> gh = mkdtemp()

    >>> def test(cmd):
    ...     run(cmd, guild_home=gh)

Deprecation warnings:

    >>> test("guild ls -o xxx")
    WARNING: option -o is deprecated and will be removed in version 0.8 - use -Fo instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -l xxx")
    WARNING: option -l is deprecated and will be removed in version 0.8 - use -Fl instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -U")
    WARNING: option -U is deprecated and will be removed in version 0.8 - use '-Fl -' instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls --unlabeled")
    WARNING: option --unlabeled is deprecated and will be removed in version 0.8 - use '--label -' instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -M")
    WARNING: option -M is deprecated and will be removed in version 0.8 - use -Fm instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -N")
    WARNING: option -N is deprecated and will be removed in version 0.8 - use -Fn instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -S today")
    WARNING: option -S is deprecated and will be removed in version 0.8 - use -Fs instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -D xxx")
    WARNING: option -D is deprecated and will be removed in version 0.8 - use -Fd instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -R")
    WARNING: option -R is deprecated and will be removed in version 0.8 - use -Sr instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -C")
    WARNING: option -C is deprecated and will be removed in version 0.8 - use -Sc instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -E")
    WARNING: option -E is deprecated and will be removed in version 0.8 - use -Se instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -T")
    WARNING: option -T is deprecated and will be removed in version 0.8 - use -St instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -P")
    WARNING: option -P is deprecated and will be removed in version 0.8 - use -Sp instead
    guild: no matching runs
    <exit 1>

    >>> test("guild ls -G")
    WARNING: option -G is deprecated and will be removed in version 0.8 - use -Sg instead
    guild: no matching runs
    <exit 1>
