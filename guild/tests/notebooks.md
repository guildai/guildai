skip-windows: yes

# Notebooks support

## nbexec

The `nbexec` module handles Notebook execution.

    >>> from guild.plugins import nbexec

### nb-repl

Flag values can be updated in Notebook cells using `nb-repl` flag
attributes.

`nb-repl` is a pattern that uses capture groups to indicate where flag
values should be inserted.

The `_replace_flag_ref` implements the replacement logic.

Here's a case where a variable assignment is updated with a new value.

    >>> nbexec._replace_flag_ref("foo = (36)", 12, "foo = 36")
    'foo = 12'

If the pattern doesn't match, the cell is left unchanged.

    >>> nbexec._replace_flag_ref("foo = (36)", 12, "foo = 42")
    'foo = 42'

Regular expressions can be used inside and outside the capture groups
as needed.

    >>> nbexec._replace_flag_ref("foo = (.*) # update me", 12, "foo = 42 # update me")
    'foo = 12 # update me'

A non-capturing group can be used to match but not replace.

    >>> nbexec._replace_flag_ref("(?:foo|bar) = (.*) # update me", 12, "foo = 42 # update me")
    'foo = 12 # update me'

Multiple groups can be used to include the flag value multiple times.

    >>> print(nbexec._replace_flag_ref("a1=(\".*\"), a2=(\".*\")", "hi", """
    ... def f(a1="a1", a2="a2"):
    ...     print(a1, a2)
    ... """))
    def f(a1='hi', a2='hi'):
        print(a1, a2)

## Running Notebooks

We use the sample 'notebooks' project.

    >>> project = Project(sample("projects", "notebooks"))

The 'add' operation adds two numbers, `x` and `y`, which can be set as
flags.

    >>> project.run("add", flags={"x": 100, "y": 200})
    [NbConvertApp] Converting notebook .../add.ipynb to notebook...
    [NbConvertApp] Converting notebook .../add.ipynb to html...

    >>> import json
    >>> generated_ipynb = json.load(open(path(project.list_runs()[0].dir, "add.ipynb")))
    >>> generated_ipynb["nbformat"]
    4

    >>> pprint(generated_ipynb["cells"])
    [{'cell_type': 'code',
      'execution_count': 1,
      'metadata': ...
      'outputs': [{'name': 'stdout',
                   'output_type': 'stream',
                   'text': ['300\n']}],
      'source': ['print(100 + 200)']}]

You can run the Notebook directly. In this case, there are no flags
because we don't know anything about the notebook.

    >>> project.run("add.ipynb")
    [NbConvertApp] Converting notebook .../add.ipynb to notebook...
    [NbConvertApp] Converting notebook .../add.ipynb to html...

    >>> project.print_runs(flags=True, labels=True)
    add.ipynb
    add        x=100 y=200  x=100 y=200

The generated Notebook is the same as the original.

    >>> generated_ipynb = json.load(open(path(project.list_runs()[0].dir, "add.ipynb")))
    >>> generated_ipynb["nbformat"]
    4

    >>> pprint(generated_ipynb["cells"])
    [{'cell_type': 'code',
      'execution_count': 1,
      'metadata': ...
      'outputs': [{'name': 'stdout',
                   'output_type': 'stream',
                   'text': ['3\n']}],
      'source': ['print(1 + 2)']}]

## Errors

    >>> project.run("invalid_language.ipynb")
    [NbConvertApp] Converting notebook .../invalid_language.ipynb to notebook
    Traceback (most recent call last):
    ...
    jupyter_client.kernelspec.NoSuchKernel: No such kernel named xxx
    <exit 1>
