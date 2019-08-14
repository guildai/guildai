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

    >>> def cp(src, select_rules, select_root=None, handler_cls=None):
    ...   dest = mkdtemp()
    ...   select = file_util.FileSelect(select_root, select_rules)
    ...   file_util.copytree(
    ...     dest, select, src,
    ...     handler_cls=handler_cls)
    ...   find(dest)

Here are the functions from `file_util` that define rules:

    >>> include = file_util.include
    >>> exclude = file_util.exclude

### Basic file selection

Here's a src containing a single text file:

    >>> src = mksrc([empty("a.txt")])
    >>> find(src)
    a.txt

Without any rules, `copytree` will not copy any files:

    >>> cp(src, [])
    <empty>

Here's a select with a single include rule that matches any file name:

    >>> cp(src, [include("*")])
    a.txt

Rules are evaluated in the order specified. The last rule to match a
file is the applied rule. Let's end our rules list with an exclude
that matches any file name:

    >>> cp(src, [include("*"), exclude("*")])
    <empty>

If we further add another include at the end of our rules list:

    >>> cp(src, [include("*"), exclude("*"), include("*")])
    a.txt

Let's create a more complex source directory structure.

    >>> src = mksrc([
    ...   empty("a.txt"),
    ...   empty("d1/a.txt"),
    ...   empty("d1/d1_1/b.txt"),
    ...   empty("d1/d1_2/c.txt"),
    ...   empty("d2/d.txt"),
    ...   empty("d2/d.yml"),
    ...   ])

Include all:

    >>> cp(src, [include("*")])
    a.txt
    d1/a.txt
    d1/d1_1/b.txt
    d1/d1_2/c.txt
    d2/d.txt
    d2/d.yml

Include only files with `.txt` extension:

    >>> cp(src, [include("*.txt")])
    a.txt
    d1/a.txt
    d1/d1_1/b.txt
    d1/d1_2/c.txt
    d2/d.txt

Include only files with `.yml` extension:

    >>> cp(src, [include("*.yml")])
    d2/d.yml

Select all files under `d1` subdirectory:

    >>> cp(src, [include("d1/*")])
    d1/a.txt
    d1/d1_1/b.txt
    d1/d1_2/c.txt

We can specify multiple patterns at once:

    >>> cp(src, [include(["d1/a.txt", "d1/d1_1/*"])])
    d1/a.txt
    d1/d1_1/b.txt

Note that a single '*' matches all files under the prefix. This is the
behavior of Python's `fnmatch` module, which Guild uses to match
files.

To select only `d1/a.txt` and ignore other files under `d1`, we can
add an exclude to our rules:

    >>> cp(src, [include("d1/*"), exclude("d1/d1*")])
    d1/a.txt

This approach relies on our foreknowledge that the other files under
`d1` are under `d1/d1`. We can be more explicit in our rules by using
regular expressions in our match.

    >>> cp(src, [include("d1/[^/]+$", regex=True)])
    d1/a.txt

### Selecting directories

Guild provides special support for selecting directories. Excluding
directories, rather than the files under the directory, has a
performance benefit as Guild doesn't have to evaluate files.

Here's a structure with a directory:

    >>> src = mksrc([
    ...   empty("d/a.txt"),
    ...   empty("b.txt"),
    ... ])

We can exclude the directory `d` this way:

    >>> cp(src, [include("*"), exclude("d", type="dir")])
    b.txt

### Selecting text or binary files

We can define a rule that selects for a particular file type: text or
binary (i.e. not text).

Let's create another source directory structure, which includes both a
text file and a binary file.

    >>> src = mksrc([
    ...   text("a.txt", 10),
    ...   binary("a.bin", 10),
    ... ])

Here's a rule that selects only text files:

    >>> cp(src, [include("*", type="text")])
    a.txt

And a rule that only selects binary files:

    >>> cp(src, [include("*", type="binary")])
    a.bin

### Skipping special directories

In some cases, a copytree operation may want to skip special
directories. These directories would include sentinels to indicate
that they should be skipped.

Here's a sample source structure that contains two such
directories. One is marked with a `.nocopy` sentinel and another
contains a file `bin/activat` (e.g. as in the case of a virtual
environment, which uses this file for activation).

    >>> src = mksrc([
    ...   empty("skip_dir/.nocopy"),
    ...   empty("skip_dir/a.txt"),
    ...   empty("skip_dir/b.txt"),
    ...   empty("venv/bin/activate"),
    ...   empty("venv/c.txt"),
    ...   empty("keep_dir/d.txt"),
    ...   empty("e.txt"),
    ... ])

To exclude `skip_dir` and `venv`, we need to indicate in our exclude
spec that we're excluding a directory (type="dir") and a pattern for
the applicable sentinel.

    >>> cp(src, [
    ...   include("*"),
    ...   exclude("*", type="dir", sentinel=".nocopy"),
    ...   exclude("*", type="dir", sentinel="bin/activate"),
    ... ])
    e.txt
    keep_dir/d.txt

We can re-enable an excluded directory this way:

    >>> cp(src, [
    ...   include("*"),
    ...   exclude("*", type="dir", sentinel=".nocopy"),
    ...   exclude("*", type="dir", sentinel="bin/activate"),
    ...   include("venv", type="dir"),
    ... ])
    e.txt
    keep_dir/d.txt
    venv/bin/activate
    venv/c.txt

### Skipping files by size

We can exclude files that are larger than a specified size.

Let's create a source directory containing two files:

    >>> src = mksrc([
    ...   empty("small.txt"),
    ...   text("large.txt", size=100),
    ... ])

Let's copy only the small file:

    >>> cp(src, [include("*", size_lt=99)])
    small.txt

And the large file:

    >>> cp(src, [include("*", size_gt=99)])
    large.txt

### Skipping files after a number of matches

A select rule may include a `max_matches` attribute, which specifies
the maximum number of matches that rule can make before it stops
matching. This is used to prevent copying unexpectedly large number of
files.

Here's a source directory containing ten files:

    >>> src = mksrc([empty("%i.txt" % i) for i in range(10)])
    >>> find(src)
    0.txt
    ...
    9.txt

Let's copy this source, but limit the number of included files to 6.

    >>> cp(src, [include("*.txt", max_matches=6)])
    0.txt
    1.txt
    2.txt
    3.txt
    4.txt
    5.txt

### Custom copytree handlers

Guild supports custom handlers for the copy tree operation. We can use
a custom handler to modify file copy and ignore behavior as well as
error handling.

Let's create a custom handler that simply logs information.

    >>> class Handler(object):
    ...
    ...   def __init__(self, src_root, dest_root, _select):
    ...     self.src_root = src_root
    ...     self.dest_root = dest_root
    ...
    ...   def copy(self, path, _rule_results):
    ...     print("copy: %s" % path)
    ...
    ...   def ignore(self, path, _rule_results):
    ...     print("ignore: %s" % path)
    ...
    ...   def handle_copy_error(self, e, src, dest):
    ...     assert False, (e, src, dest)

Our source directory:

    >>> src = mksrc([
    ...   empty("a.txt"),
    ...   binary("a.bin", size=1),
    ... ])

We specify the class for our handler in the call to `copytree`.

    >>> cp(src, [include("*")], handler_cls=Handler)
    copy: a.bin
    copy: a.txt
    <empty>

    >>> cp(src, [include("*.bin")], handler_cls=Handler)
    copy: a.bin
    ignore: a.txt
    <empty>

    >>> cp(src, [include("*", size_lt=1)], handler_cls=Handler)
    ignore: a.bin
    copy: a.txt
    <empty>

### Symlinks

TODO

### Alternative source roots

TODO

### Validation

Valid and invalid rule types:

    >>> _ = include("*", type=None)
    >>> _ = include("*", type="text")
    >>> _ = include("*", type="binary")
    >>> _ = include("*", type="dir")
    >>> _ = include("*", type="invalid")
    Traceback (most recent call last):
    ValueError: invalid value for type 'invalid': expected one of text,
    binary, dir
