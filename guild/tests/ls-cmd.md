# ls command

The ls command is used to list run files.

We'll use an args proxy to simulate command arguments.

    >>> class Args(object):
    ...   def __init__(self, run="1", path=None, full_path=False,
    ...                no_format=None, follow_links=False, all=False,
    ...                source=False, marked=False, unmarked=False):
    ...       self.run = run
    ...       self.path = path
    ...       self.full_path = full_path
    ...       self.source = source
    ...       self.no_format = no_format
    ...       self.follow_links = follow_links
    ...       self.all = all
    ...       self.ops = ()
    ...       self.labels = ()
    ...       self.unlabeled = False
    ...       self.marked = marked
    ...       self.unmarked = unmarked

To test list with a run containing symbolic links, we need to generate
a sample run dynamically. We can't use a sample directory structure
with links because the links will not be preserved when the directory
is packaged with setuptools.

Let's create a sample run structure:

    >>> from guild import run as runlib
    >>> guild_home = mkdtemp()
    >>> runs_home = join_path(guild_home, "runs")
    >>> mkdir(runs_home)
    >>> run = runlib.Run("run-1", join_path(runs_home, "run-1"))
    >>> run.init_skel()
    >>> run.write_encoded_opref("guildfile:. abc123 foo bar")
    >>> touch(join_path(run.path, "a"))
    >>> touch(join_path(run.path, "b"))
    >>> mkdir(join_path(run.path, "c"))
    >>> touch(join_path(run.path, "c", "d.txt"))
    >>> touch(join_path(run.path, "c", "e.txt"))
    >>> touch(join_path(run.path, "c", "f.bin"))
    >>> symlink("c", join_path(run.path, "l"))
    >>> touch(join_path(run.path, ".guild", "attrs", "exit_status"))
    >>> touch(join_path(run.path, ".guild", "some-guild-file"))
    >>> mkdir(join_path(run.path, ".guild", "source"))
    >>> touch(join_path(run.path, ".guild", "source", "a.py"))
    >>> touch(join_path(run.path, ".guild", "source", "guild.yml"))

Here's a function that tests the ls command using sample runs.

    >>> from guild import config
    >>> from guild.commands import ls_impl

    >>> def ls(**kw):
    ...     with config.SetGuildHome(guild_home):
    ...         ls_impl.main(Args(**kw), None)

By default ls prints all non-Guild files without following links:

    >>> ls()
    /.../runs/run-1:
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/

We can list various paths:

    >>> ls(path="a")
    /.../runs/run-1:
      a

    >>> ls(path="c")
    /.../runs/run-1:
      c/
      c/d.txt
      c/e.txt
      c/f.bin

    >>> ls(path="*.txt")
    /.../runs/run-1:
      c/d.txt
      c/e.txt

    >>> ls(path="no-match")
    /.../runs/run-1:

Follow links:

    >>> ls(follow_links=True)
    /.../runs/run-1:
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
    /.../runs/run-1:
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
    /.../runs/run-1/a
    /.../runs/run-1/b
    /.../runs/run-1/c
    /.../runs/run-1/c/d.txt
    /.../runs/run-1/c/e.txt
    /.../runs/run-1/c/f.bin
    /.../runs/run-1/l

Show all files, including Guild files:

    >>> ls(all=True)
    /.../runs/run-1:
      .guild/
      .guild/attrs/
      .guild/attrs/exit_status
      .guild/attrs/initialized
      .guild/opref
      .guild/some-guild-file
      .guild/source/
      .guild/source/a.py
      .guild/source/guild.yml
      a
      b
      c/
      c/d.txt
      c/e.txt
      c/f.bin
      l/

Show source files:

    >>> ls(source=True)
    /.../runs/run-1:
      .guild/source/
      .guild/source/a.py
      .guild/source/guild.yml

Source with fill path:

    >>> ls(source=True, full_path=True)
    /.../runs/run-1/.guild/source
    /.../runs/run-1/.guild/source/a.py
    /.../runs/run-1/.guild/source/guild.yml

Source with path:

    >>> ls(source=True, path="a.*")
    /.../runs/run-1:
      .guild/source/a.py
