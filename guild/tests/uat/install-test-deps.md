# Install test dependencies

Tests require additional packages that are not included in the Guild
distribution or requirements.txt. They are defined in
requirements-test.txt.

    >>> quiet("pip install -r $GUILD_PKGDIR/guild/tests/requirements.txt")
