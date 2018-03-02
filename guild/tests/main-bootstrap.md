# Main bootstrap

Guild ships with a number of third party packages under a subdirectory
named 'external'. These packages must be made available on the system
path before Guild can run properly. `main_bootstrap` performs this
init before calling the Guild main function.

    >>> from guild import main_bootstrap

In addition to setting up the system path, `main_bootstrap` verifies
that Guild's dependencies are resolved and prints user facing messages
if any requirement is missing.

The order that required packages is checked is important to the
user. The package 'pip' must be checked first because it's used to
install other required packages.

The internal function `_sort_reqs` handles this.

Here is the order that Guild requirements are checked:

    >>> import guild
    >>> pprint(main_bootstrap._sort_reqs(guild.__requires__))
    [('pip', 'pip'),
     ('setuptools', 'setuptools'),
     ('six', 'six'),
     ('tabview', 'tabview'),
     ('twine', 'twine'),
     ('werkzeug', 'Werkzeug'),
     ('whoosh', 'Whoosh'),
     ('yaml', 'PyYAML')]

Here's a fake list where pip is listed first:

    >>> pprint(main_bootstrap._sort_reqs([
    ...   ("a", "a"),
    ...   ("b", "b"),
    ...   ("z", "z"),
    ...   ("pip", "pip")
    ... ]))
    [('pip', 'pip'), ('a', 'a'), ('b', 'b'), ('z', 'z')]
