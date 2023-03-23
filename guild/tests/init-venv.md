## Initialzing a virtual environment

`guild init` creates a new Python virtual environment when either
`--venv` is specified or any of the virtual environment related
options are specified.

The init params that imply a virtual environment are defined in
`guild.commands.init_impl.VENV_IMPLIES`.

    >>> from guild.commands import init_impl

    >>> pprint(init_impl.VENV_IMPLIES)  # doctest: +REPORT_UDIFF
    ('name',
     'python',
     'guild',
     'system_site_packages',
     'requirements',
     'path',
     'no_reqs',
     'pre_release')

Guild prompts the user showing the venv params before creating a
virtual environment.

    >>> cd(mkdtemp())
    >>> run("guild init --venv", timeout=2)
    You are about to initialize a Guild environment:
      Location: ...guild-test-.../venv
      Name: guild-test-...
      Python interpreter: default
      Use system site packages: no
      Guild: ...
      Resource cache: shared
    Continue? (Y/n)
    <exit ...>

When creating a virtual environment, Guild installs the requirements
specified in `requirements.txt` by default. Guild supports a special
comment that specifies the Python version requirements for the
environment. The comment must contain `python<req>` where `req` is a
valid Python package [requirements
spec](https://peps.python.org/pep-0508/).

Here's an invalid spec in a requirements file.

    >>> write("requirements.txt", """
    ... # python=1
    ... """)

    >>> run("guild init --venv", timeout=2)
    guild: invalid Python requirement '=1' in ./requirements.txt
    Modify the requirement in that file or use '--python <version>'
    to provide an explicit version.
    <exit 1>

We can bypass the issue by specifying `--python`. This option implies
`--venv` so we can omit the option.

    >>> run("guild init --python 3", timeout=2)
    You are about to initialize a Guild environment:
      Location: ...guild-test-.../venv
      Name: guild-test-...
      Python interpreter: ...
      Use system site packages: no
      Guild: ...
      Python requirements:
        ./requirements.txt
      Resource cache: shared
    Continue? (Y/n)
    <exit ...>

Create a requirements file with a valid spec. Include an incidental
Python package to install.

    >>> write("requirements.txt", """
    ... # python>=3.6,<4
    ... chardet
    ... """)

Preview the init operation using the default values.

    >>> run("guild init --venv", timeout=2)
    You are about to initialize a Guild environment:
      Location: ...guild-test-.../venv
      Name: guild-test-...
      Python interpreter: ...
      Use system site packages: no
      Guild: ...
      Python requirements:
        ./requirements.txt
      Resource cache: shared
    Continue? (Y/n)
    <exit ...>

Create the environment.

    >>> run("guild init --venv -y")  # doctest: -WINDOWS
    Initializing Guild environment in ...guild-test-.../venv
    Creating virtual environment
    ...
    Upgrading pip
    Installing Guild ...
    ...
    Guild environment initialized in ...guild-test-.../venv
    <BLANKLINE>
    To activate it run:
    <BLANKLINE>
      source guild-env

On Windows instruction to activate the environment (last line) is
different from POSIX systems.

    >>> run("guild init --venv -y")  # doctest: +WINDOWS_ONLY
    Initializing Guild environment in ...guild-test-.../venv
    Creating virtual environment
    ...
    Upgrading pip
    Installing Guild ...
    ...
    Guild environment initialized in ...guild-test-.../venv
    <BLANKLINE>
    To activate it run:
    <BLANKLINE>
      .../guild-test-.../venv/Scripts/activate

Verify that `chardet` is installed in the virtual env.

    >>> run("venv/bin/python -c 'import chardet; print(chardet.__file__)'")
    ???guild-test-.../venv/lib/python.../site-packages/chardet/__init__.py
