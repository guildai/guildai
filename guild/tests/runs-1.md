## Runs

Runs are represented by the class `guild.run.Run`.

    >>> import guild.run

They are used to manage information in a run directory. For our tests
we'll create a temporary directory that represents our run directory:

    >>> run_dir = mkdtemp()

Runs have IDs that uniquely identify them. The `mkdir` function can be
used to generate unique run IDs.

    >>> run = guild.run.Run(guild.run.mkid(), run_dir)

### Run IDs

Unique run IDs are 32 chars long:

    >>> len(run.id)
    32

Runs have short IDs, which are 8 chars long:

    >>> len(run.short_id)
    8

### Run directory files

We can iterate files under a run directory using the `iter_files`
method. For our tests we'll use a helper that normalizes output for
our tests:

    >>> def run_files(run):
    ...   return sorted([
    ...     relpath(path, run_dir)
    ...     for path in run.iter_files(all_files=True)
    ...   ])

We can iterate files under a run directory. Initially the directory is
empty:

    >>> run_files(run)
    []

We can initialize the run directory using `init_skel`:

    >>> run.init_skel()
    >>> run_files(run)
    ['.guild', '.guild/attrs', '.guild/attrs/initialized']

Note that Guild manages files under a run directory inside a `.guild`
directory ("guild directory").

### Run attributes

Run attributes are stored in the `attrs` guild sub-directory.

We can iterate attributes using `iter_attrs`:

    >>> list(run.iter_attrs())
    [('initialized', ...)]

We can read attribute values as run items or using the `get` method:

    >>> run["msg"]
    Traceback (most recent call last):
    KeyError: 'msg'

    >>> print(run.get("msg"))
    None

    >>> run.get("msg", "no msg!")
    'no msg!'

We can write them using the `write_attr` method:

    >>> run.write_attr("msg", "hello")

Here are the run files after writing the attribute:

    >>> run_files(run)
    ['.guild',
     '.guild/attrs',
     '.guild/attrs/initialized',
     '.guild/attrs/msg']

And the value of our attribute:

    >>> run["msg"]
    'hello'

    >>> run.get("msg")
    'hello'

We can store attributes provided they're primitive Python
types. Values are encoded using YAML. Let's create a helper function
that shows us the attribute file contents.

    >>> def cat_attr(name):
    ...   cat(run_dir, ".guild", "attrs", name)

Here's the encoding of a string attribute:

    >>> cat_attr("msg")
    hello

Integer:

    >>> run.write_attr("int", 123)
    >>> run["int"]
    123
    >>> cat_attr("int")
    123

Float:

    >>> run.write_attr("float", 123.456)
    >>> run["float"]
    123.456
    >>> cat_attr("float")
    123.456

None:

    >>> run.write_attr("none", None)
    >>> print(run["none"])
    None
    >>> cat_attr("none")
    null

List:

    >>> run.write_attr("list", [1, 2, 3, 4.567, "foo", "bar"])
    >>> run["list"]
    [1, 2, 3, 4.567, 'foo', 'bar']
    >>> cat_attr("list")
    - 1
    - 2
    - 3
    - 4.567
    - foo
    - bar

Tuples (stored and returned as lists):

    >>> run.write_attr("tuple", (1, 2, 3, "foo"))
    >>> run["tuple"]
    [1, 2, 3, 'foo']
    >>> cat_attr("tuple")
    - 1
    - 2
    - 3
    - foo

Dict:

    >>> run.write_attr("dict", {"num": 123, "str": "hello", "float": 123.456})
    >>> pprint(run["dict"])
    {'float': 123.456, 'num': 123, 'str': 'hello'}
    >>> cat_attr("dict")
    float: 123.456
    num: 123
    str: hello

List of lists:

    >>> run.write_attr("lol", [["num", 123],
    ...                        ["str", "hello"],
    ...                        ["float", 123.456]])
    >>> run["lol"]
    [['num', 123], ['str', 'hello'], ['float', 123.456]]
    >>> cat_attr("lol")
    - - num
      - 123
    - - str
      - hello
    - - float
      - 123.456

List of tuples (stored and returned as list of lists):

    >>> run.write_attr("tuple-list", [("foo", 123), ("bar", 456)])
    >>> run["tuple-list"]
    [['foo', 123], ['bar', 456]]
    >>> cat_attr("tuple-list")
    - - foo
      - 123
    - - bar
      - 456

Non-primitive values can't be written as run attributes:

    >>> run.write_attr("module", guild.run)
    Traceback (most recent call last):
    RepresenterError: ...

    >>> run.write_attr("function", cat_attr)
    Traceback (most recent call last):
    RepresenterError: ...

    >>> class Foo(object):
    ...   pass
    >>> run.write_attr("class", Foo)
    Traceback (most recent call last):
    RepresenterError: ...

## Managing runs

Runs are managed by the `var` module:

    >>> import guild.var

We can list runs using the `list_runs` function. By default
`list_runs` enumerates runs in the system location
(i.e. `~/.guild/runs`). For our tests we'll use the sample location.

Here's a helper function to list runs in that location:

    >>> def runs(**kw):
    ...     sample_runs = sample("runs")
    ...     return guild.var.runs(root=sample_runs, **kw)

By default runs are returned unsorted (based on how they're read from
the file system). We can can sort by various run attributes using the
`sort` argument. Here we order by id in reverse order:

    >>> [run.id for run in runs(sort=["-id"])]
    ['7d145216ae874020b735f001a7bfd27d',
     '42803252919c495cbd65f292f1f156a0',
     '360192fdf9b74f2fad5f514e9f2fdadb']

Sort by operation, then date:

    >>> [(run.short_id, str(run.opref), run["started"])
    ...  for run in runs(sort=["opref", "started"])]
    [('42803252', "test:'' '' mnist evaluate", 1506790419000000),
     ('360192fd', "test:'' '' mnist train", 1506790385000000),
     ('7d145216', "test:'' '' mnist train", 1506790401000000)]

Sort by date, latest first:

    >>> [(run.short_id, run["started"])
    ...  for run in runs(sort=["-started"])]
    [('42803252', 1506790419000000),
     ('7d145216', 1506790401000000),
     ('360192fd', 1506790385000000)]

## Run filters

We can filter runs by specifying a `filter` argument to the `runs`
function. A filter is a function that takes a run as a single argument
and returns True if the run should be returned or False if it should
not be returned.

Here we'll filter runs with an exist_status of "0" (i.e. run
successfully to completion):

    >>> [(run.short_id, run["exit_status"])
    ...  for run in runs(filter=lambda r: r.get("exit_status") == 0)]
    [('42803252', 0)]

`guild.var` provides a helper function that returns various named
filters:

- attr - true if a run attribute matches an expected value
- all - true if all filters are true
- any - true if any filters are true

Filter names may be preceded by '!' to negate them.

Here is the same filter as above, but using `run_filter`:

    >>> filter = guild.var.run_filter("attr", "exit_status", 0)
    >>> [(run.short_id, run["exit_status"]) for run in runs(filter=filter)]
    [('42803252', 0)]

Here's a list of runs with an exit_status not equals to "0":

    >>> filter = guild.var.run_filter("!attr", "exit_status", 0)
    >>> [(run.short_id, run.get("exit_status"))
    ...  for run in runs(filter=filter, sort=["id"])]
    [('360192fd', None), ('7d145216', 1)]

Runs with op equal to "mnist:evaluate" and exit_status equal to "0"
(i.e. successful evaluate operations):

    >>> filter = guild.var.run_filter(
    ...   "all",
    ...   [guild.var.run_filter("attr", "exit_status", 0)])
    >>> [(run.short_id, run.get("exit_status")) for run in runs(filter=filter)]
    [('42803252', 0)]

Runs with exit_status equal to "0" or "1":

    >>> filter = guild.var.run_filter(
    ...   "any",
    ...   [guild.var.run_filter("attr", "exit_status", 0),
    ...    guild.var.run_filter("attr", "exit_status", 1)])
    >>> [(run.short_id, run.get("exit_status"))
    ...  for run in runs(filter=filter, sort=["id"])]
    [('42803252', 0), ('7d145216', 1)]
