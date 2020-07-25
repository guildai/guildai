# Running a script on a remote

Guild doesn't support running scripts on a remote. The operation must
be defined in a Guild file.

    >>> cd(example("hello"))

    >>> run("guild run say.py -r guild-uat -y")
    guild: cannot run scripts remotely
    Define an operation in guild.yml that uses say.py as the main module
    and run that operation instead.
    <exit 1>
