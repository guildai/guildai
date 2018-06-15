# Workflow

## Basics

    >>> from guild import workflow as wf

    >>> class TestNode(wf.Node):
    ...
    ...   def __init__(self, msg, desc):
    ...     self.msg = msg
    ...     self.desc = desc
    ...
    ...   def get_description(self):
    ...     return self.desc
    ...
    ...   def run(self):
    ...     print(self.msg)

    >>> def preview_run(g):
    ...    for n in graph.run_order():
    ...      print("- " + n.get_description())

Hello workflow node:

    >>> hello = TestNode("Hello workflow", "say hello")

    >>> hello.run()
    Hello workflow

Using a graph:

    >>> graph = wf.Graph()
    >>> graph.add_node(hello)
    >>> preview_run(graph)
    - say hello

Dependencies:

    >>> hello_setup = TestNode("Hello setup", "setup hello")
    >>> graph.add_dep(hello_setup, hello)
    >>> preview_run(graph)
    - setup hello
    - say hello

## Scenario 1 - simple "copy file" operation

In this scenario, we'll run an operation that has a single file
dependency and creates a copy of that file in the run directory.

We'll use the "copy-file" sample project:

    >>> from guild import guildfile
    >>> gf = guildfile.from_dir(sample("projects/copy-file"))

And run the "test:copy-file" operation:

    >>> opdef = gf.models["test"].get_operation("copy-file")
    >>> opdef.fullname
    'test:copy-file'

We need a run directory:

    >>> run_dir = mkdtemp()

Our op:

    >>> import guild.op
    >>> copy_file_op = guild.op.Operation(
    ...   ("guildfile", gf.dir, "", "test"),
    ...   opdef,
    ...   run_dir)

The op is wrapped in an op node:

    >>> from guild.workflow import op_node
    >>> copy_file_node = op_node.OpNode(copy_file_op, quiet=True)
    >>> copy_file_node.get_description()
    "Run 'test:copy-file'"

The op node is included in a workflow graph with dependencies:

    >>> graph = wf.Graph()
    >>> graph.add_node(copy_file_node, with_deps=True)

We can preview the operation, which includes op dependencies:

    >> preview_run(graph)
    - Initialize 'test:copy-file'
    - Resolve source 'file.txt'
    - Resolve resource 'file'
    - Run 'test:copy-file'

Before running the op and its dependencies, let's confirm the run dir
is empty:

    >> dir(run_dir)
    []

And finally we run the op along with its dependencies:

    >> for node in graph.run_order():
    ...   node.run()

Here's the result in run dir:

    >> dir(run_dir)
    ['.guild', 'copy.txt', 'file.txt']

And the output of various files:

    >> cat(join_path(run_dir, "file.txt"))
    Sample file
    <BLANKLINE>

    >> cat(join_path(run_dir, "copy.txt"))
    Sample file
    <BLANKLINE>

    >> cat(join_path(run_dir, ".guild", "output"))
    Copying file.txt to copy.txt
    <BLANKLINE>
