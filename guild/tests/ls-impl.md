---
doctest: -WINDOWS
---

# ls command impl

These tests show the behavior of the list run file implementation.

    >>> from guild.commands.ls_impl import list_run_files

Create a sample directory structure to test.

    >>> dir = mkdtemp()
    >>> mkdir(join_path(dir, "aaa"))
    >>> mkdir(join_path(dir, "aaa", "bb"))
    >>> touch(join_path(dir, "aaa", "bb", "c"))
    >>> touch(join_path(dir, "aaa", "bb", ".d"))
    >>> mkdir(join_path(dir, ".eee"))
    >>> touch(join_path(dir, ".eee", "ff"))
    >>> mkdir(join_path(dir, ".eee", "gg"))
    >>> touch(join_path(dir, ".eee", "gg", "i"))
    >>> mkdir(join_path(dir, ".eee", ".jj"))
    >>> touch(join_path(dir, ".eee", ".jj", "k"))

    >>> from guild import run as runlib
    >>> run_proxy = runlib.for_dir(dir)

    >>> find(dir)
    .eee/.jj/k
    .eee/ff
    .eee/gg/i
    aaa/bb/.d
    aaa/bb/c

Create a helper function to list files.

    >>> class Args:
    ...     def __init__(self, **kw):
    ...         for name in kw:
    ...             setattr(self, name, kw[name])

    >>> def ls(path=None, all=False, follow_links=False, full_path=False):
    ...     args = Args(
    ...         path=path,
    ...         all=all,
    ...         follow_links=follow_links,
    ...         full_path=full_path,
    ...         sourcecode=False,
    ...         generated=False,
    ...         dependencies=False)
    ...     for name in sorted(list_run_files(run_proxy, args)):
    ...         print(name)

Default file listing:

    >>> ls()
    aaa
    aaa/bb
    aaa/bb/c

All files:

    >>> ls(all=True)
    .eee
    .eee/.jj
    .eee/.jj/k
    .eee/ff
    .eee/gg
    .eee/gg/i
    aaa
    aaa/bb
    aaa/bb/.d
    aaa/bb/c

All files with pattern:

    >>> ls(all=True, path=".eee")
    .eee
    .eee/.jj
    .eee/.jj/k
    .eee/ff
    .eee/gg
    .eee/gg/i

Top-level dir pattern:

    >>> ls(path="aaa")
    aaa
    aaa/bb
    aaa/bb/c

A partial path doesn't match:

    >>> ls(path="aa")

Subdir patterns:

    >>> ls(path="aaa/bb")
    aaa/bb
    aaa/bb/c

    >>> ls(path="aaa/bb/c")
    aaa/bb/c

    >>> ls(path="a/xxx")

Selecting a hidden dir with a pattern:

    >>> ls(path=".eee")
    .eee
    .eee/ff
    .eee/gg
    .eee/gg/i

    >>> ls(path=".eee", all=True)
    .eee
    .eee/.jj
    .eee/.jj/k
    .eee/ff
    .eee/gg
    .eee/gg/i

    >>> ls(path=".eee/gg")
    .eee/gg
    .eee/gg/i

    >>> ls(path=".eee/.jj")
    .eee/.jj
    .eee/.jj/k

Glob style patterns:

    >>> ls(path="*")
    aaa
    aaa/bb
    aaa/bb/c

    >>> ls(path="*", all=True)
    .eee
    .eee/.jj
    .eee/.jj/k
    .eee/ff
    .eee/gg
    .eee/gg/i
    aaa
    aaa/bb
    aaa/bb/.d
    aaa/bb/c

    >>> ls(path="aaa/*")
    aaa/bb
    aaa/bb/c

    >>> ls(path="a*")
    aaa
    aaa/bb
    aaa/bb/c

    >>> ls(path="a*", all=True)
    aaa
    aaa/bb
    aaa/bb/.d
    aaa/bb/c

    >>> ls(path=".e*")
    .eee
    .eee/ff
    .eee/gg
    .eee/gg/i

    >>> ls(path=".e*/.j*")
    .eee/.jj
    .eee/.jj/k
