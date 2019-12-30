# Locks

Guild supports system wide locks via the `guild.lock` module.

    >>> from guild import lock

Locks are file based and stored under the `locks` subdirectory of
Guild home.

Here's a Guild home for our tests:

    >>> guild_home = mkdtemp()

Here's a helper function that creates a lock in Guild home and that
specifies a short default timeout.

    >>> def mklock(name):
    ...     return lock.Lock(name, timeout=1, guild_home=guild_home)

Locks are created using a name:

    >>> l = mklock("test-1")

Note the location of the lock file:

    >>> l.lock_file == os.path.join(guild_home, "locks", "test-1")
    True

Initially a lock is not acquired:

    >>> l.is_locked
    False

We can acquire a lock using a context manager:

    >>> with l:
    ...     l.is_locked
    True

    >>> l.is_locked
    False

Or using the `acquire` method:

    >>> _ = l.acquire()
    >>> l.is_locked
    True

Use `release` to release the lock:

    >>> l.release()
    >>> l.is_locked
    False

If a lock is acquired, it cannot be acquired by another process until
it's released.

    >>> _ = l.acquire()
    >>> l.is_locked
    True

Let's attempt to acquire the lock.

    >>> l2 = mklock("test-1")

Again, the lock is not initially acquired.

    >>> l2.is_locked
    False

Let's attempt to acquire it.

    >>> l2.acquire()
    Traceback (most recent call last):
    Timeout: The file lock '.../locks/test-1' could not be acquired.

Let's release the lock and try again.

    >>> l.release()
    >>> l.is_locked
    False

    >>> _ = l2.acquire()
    >>> l2.is_locked
    True

Note that if we try to acquire the lock from our first lock, we can't:

    >>> l.acquire()
    Traceback (most recent call last):
    Timeout: The file lock '.../locks/test-1' could not be acquired.

Let's create another lock.

    >>> l3 = mklock("test-2")

We can acquire it without conflict.

    >>> _ = l3.acquire()
    >>> l3.is_locked
    True

Let's release our locks:

    >>> for lock in [l, l2, l3]:
    ...     lock.release()
    ...     assert not lock.is_locked, lock

Lock files are intentionally not removed on non-Windows.

    >>> find(guild_home)  # doctest: -WINDOWS
    locks/test-1
    locks/test-2

They are removed on Windows:

    >>> find(guild_home)  # doctest: +WINDOWS_ONLY
    <empty>
