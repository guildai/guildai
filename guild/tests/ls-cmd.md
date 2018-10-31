# ls command

The ls command is used to list run files.

We'll use an args proxy to simulate command arguments.

    >>> class Args(object):
    ...   def __init__(self, run="1", path=None, full_path=False,
    ...                no_format=None, follow_links=False, all=False):
    ...       self.run = run
    ...       self.path = path
    ...       self.full_path = full_path
    ...       self.no_format = no_format
    ...       self.follow_links = follow_links
    ...       self.all = all
    ...       self.ops = ()
    ...       self.labels = ()
    ...       self.unlabeled = False

Here's a function that tests the ls command using sample runs.

    >>> from guild import config
    >>> from guild.commands import ls_impl

    >>> def ls(**kw):
    ...     with config.SetGuildHome(sample("ls-runs-home")):
    ...         ls_impl.main(Args(**kw), None)

By default ls prints all non-Guild files without following links:

    >>> ls()
    ~/.../samples/ls-runs-home/runs/run-1:
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/

We can list various paths:

    >>> ls(path="a")
    ~/.../samples/ls-runs-home/runs/run-1:
      a

    >>> ls(path="c")
    ~/.../samples/ls-runs-home/runs/run-1:
      c/
      c/d.txt
      c/e.txt
      c/f.bin

    >>> ls(path="*.txt")
    ~/.../samples/ls-runs-home/runs/run-1:
      c/d.txt
      c/e.txt

    >>> ls(path="no-match")
    ~/.../samples/ls-runs-home/runs/run-1:

Follow links:

    >>> ls(follow_links=True)
    ~/.../samples/ls-runs-home/runs/run-1:
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/
      l/d.txt
      l/e.txt
      l/f.bin

    >>> ls(follow_links=True, path="*.bin")
    ~/.../samples/ls-runs-home/runs/run-1:
      c/f.bin
      l/f.bin

Show without formatting:

    >>> ls(no_format=True)
    a
    b
    c/
    c/d.txt
    c/e.txt
    c/f.bin
    l/

Show full path:

    >>> ls(full_path=True)
    /.../samples/ls-runs-home/runs/run-1/a
    /.../samples/ls-runs-home/runs/run-1/b
    /.../samples/ls-runs-home/runs/run-1/c
    /.../samples/ls-runs-home/runs/run-1/c/d.txt
    /.../samples/ls-runs-home/runs/run-1/c/e.txt
    /.../samples/ls-runs-home/runs/run-1/c/f.bin
    /.../samples/ls-runs-home/runs/run-1/l

Show all files, including Guild files:

    >>> ls(all=True)
    ~/SCM/.../samples/ls-runs-home/runs/run-1:
      .guild/
      .guild/attrs/
      .guild/attrs/opref
      .guild/e
      .guild/f
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/
