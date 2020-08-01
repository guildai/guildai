# TF Events

Support for reading summaries from TF event files is provided by
`guild.tfevent`.

    >>> from guild import tfevent

## Basic event writing and reading

We can log TF events are using `guild.summary.SummaryWriter`.

    >>> from guild.summary import SummaryWriter

We'll create our events log in a temp diretory:

    >>> logdir = mkdtemp()
    >>> dir(logdir)
    []

Our writer:

    >>> writer = SummaryWriter(logdir)

We can use writer to write scalars:

    >>> writer.add_scalar("a", 1.0)
    >>> writer.add_scalar("b", 2.0)
    >>> writer.add_scalar("c", 3.0)

and close the writer:

    >>> writer.close()

The logdir:

    >>> logged = dir(logdir)
    >>> logged
    ['events.out.tfevents...']

We can read the events using `guild.tfevent.ScalarReader` to read back
scalars.

First let's import `tfevent` and patch TensorBoard logging to avoid
noise in our logs.

    >>> tfevent._ensure_tb_logging_patched()

Here's a scalar reader for our log dir:

    >>> reader = tfevent.ScalarReader(logdir)

And the scalars:

    >>> list(reader)
    [('a', 1.0, 0),
     ('b', 2.0, 0),
     ('c', 3.0, 0)]

## ScalarReader and subdirectories

`ScalarReader` only reads events from the specified directory and will
not read events from subdirectories.

Here's a new log dir:

    >>> basedir = mkdtemp()

And a subdirectory:

    >>> subdir = join_path(basedir, "subdir")
    >>> mkdir(subdir)

Let's write some events into the subdirectory:

    >>> subdir_writer = SummaryWriter(subdir)
    >>> subdir_writer.add_scalar("a", 4.0)
    >>> subdir_writer.add_scalar("b", 5.0)
    >>> subdir_writer.add_scalar("c", 6.0)
    >>> subdir_writer.close()

The generated files:

    >>> find(basedir)
    subdir/events.out.tfevents...

We can load the events from the subdirectory as expected:

    >>> subdir_reader = tfevent.ScalarReader(subdir)
    >>> list(subdir_reader)
    [('a', 4.0, 0),
     ('b', 5.0, 0),
     ('c', 6.0, 0)]

However, events from the base log directory are empty:

    >>> basedir_reader = tfevent.ScalarReader(basedir)
    >>> list(basedir_reader)
    []

## `tfevent.scalar_readers` basic use

We can use `tfevent.scalar_readers` to iterate over all events,
including those in subdirectories.

We'll use our prior example as a starting point.

Here is the directory structure:

    >>> find(basedir)
    subdir/events.out.tfevents...

`tfevent.scalar_readers()` is a generator that yields tuples of
directory, digest, and reader.

Here's our the scalars under `basedir`.

    >>> readers = list(tfevent.scalar_readers(basedir))
    >>> len(readers)
    1

Our one reader is for `subdir`:

    >>> readers[0][0]
    '.../subdir'

The scalars:

    >>> for dir, digest, reader in readers:
    ...     for s in reader:
    ...         print(s)
    ('a', 4.0, 0)
    ('b', 5.0, 0)
    ('c', 6.0, 0)

The digest changes when we write new scalars to a directory.

Here's the current digest:

    >>> digest0 = readers[0][1]

Let's write more scalars to subdir (we wait a second to ensure the TF
event filename timestamp is incremented):

    >>> sleep(1)
    >>> subdir_writer = SummaryWriter(subdir)
    >>> subdir_writer.add_scalar("d", 7.0)
    >>> subdir_writer.add_scalar("e", 8.0)
    >>> subdir_writer.close()

This generates a new log file:

    >>> find(basedir)
    subdir/events.out.tfevents...
    subdir/events.out.tfevents...

Re-reading from `basedir`:

    >>> readers = list(tfevent.scalar_readers(basedir))
    >>> len(readers)
    1

Our one reader is for `subdir`:

    >>> readers[0][0]
    '/.../subdir'

And the scalars:

    >>> for dir, digest, reader in readers:
    ...     for s in reader:
    ...         print(s)
    ('a', 4.0, 0)
    ('b', 5.0, 0)
    ('c', 6.0, 0)
    ('d', 7.0, 0)
    ('e', 8.0, 0)

The current digest:

    >>> digest1 = readers[0][1]

It's different from the previous digest:

    >>> digest0 != digest1
    True

## `tfevent.scalar_readers` and symlinks

`scalar_readers` does not include scalars in symlinked directories.

Let's link `subdir` to `subdir_link`:

    >>> subdir_link = join_path(basedir, "subdir_link")
    >>> symlink("subdir", subdir_link)

Our directory structure:

    >>> find(basedir, followlinks=True)
    subdir/events.out.tfevents...
    subdir/events.out.tfevents...
    subdir_link
    subdir_link/events.out.tfevents...
    subdir_link/events.out.tfevents...

And our readers:

    >>> readers = list(tfevent.scalar_readers(basedir))
    >>> len(readers)
    1

    >>> readers[0][0]
    '/.../subdir'

    >>> for dir, digest, reader in readers:
    ...     for s in reader:
    ...         print(s)
    ('a', 4.0, 0)
    ('b', 5.0, 0)
    ('c', 6.0, 0)
    ('d', 7.0, 0)
    ('e', 8.0, 0)
