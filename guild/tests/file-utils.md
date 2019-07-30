# File Utils

The module `guild.file_util` implements advanced file utilities.

    >>> from guild import file_util

## Copy tree

The function `file_util.copytree` is an advanced version of
`guild.util.copytree` that uses a flexible file select scheme for
selecting files from a root location to copy to a destination
directory.

`copytree` is driven by a `file_util.FileSelect` instance, which
specifies:

- A root location to copy from
- Select configuration

Select configuration is a list of rules, which can exclude or include
files based on file attributes:

- Name
- Size
- Type (text file, binary file, or directory)
- Number of files previously selected by the rule

For our tests, we generate a source directory and copy files from it
to a destination directory.

Here's a facility for generating a source directory of files to copy:

    >>> from guild import util

    >>> class file_base(object):
    ...   def __init__(self, path, write_mode, base_char, size):
    ...     self.path = path
    ...     self.write_mode = write_mode
    ...     self.base_char = base_char
    ...     self.size = size
    ...
    ...   def mk(self, root):
    ...     path = os.path.join(root, self.path)
    ...     util.ensure_dir(os.path.dirname(path))
    ...     with open(path, "w" + self.write_mode) as f:
    ...       f.write(self.base_char * self.size)

    >>> def empty(path):
    ...   return text(path)

    >>> def text(path, size=0):
    ...   return file_base(path, "", "0", size)

    >>> def binary(path, size):
    ...   return file_base(path, "b", b"\x01", size)

    >>> def mksrc(specs):
    ...   src = mkdtemp()
    ...   for spec in specs:
    ...     spec.mk(src)
    ...   return src

Here's a function to copy a directory using `copytree`:

    >>> def cp(src, select_rules, select_root=None):
    ...   dest = mkdtemp()
    ...   select = file_util.FileSelect(select_root, select_rules)
    ...   file_util.copytree(dest, select, src)
    ...   find(dest)

Here are the functions from `file_util` that define rules:

    >>> include = file_util.include
    >>> exclude = file_util.exclude

## Basic file selection

Here's a src containing a single text file:

    >>> src = mksrc([empty("a.txt")])
    >>> find(src)
    a.txt

Without any rules, `copytree` will not copy any files:

    >>> cp(src, [])

Here's a select with a single include rule that matches any file name:

    >>> cp(src, [include("*")])
    a.txt

Rules are evaluated in the order specified. The last rule to match a
file is the applied rule. Let's end our rules list with an exclude
that matches any file name:

    >>> cp(src, [include("*"), exclude("*")])

If we further add another include at the end of our rules list:

    >>> cp(src, [include("*"), exclude("*"), include("*")])
    a.txt
