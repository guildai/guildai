# Init default project

A project using the default template can be initialized using `guild
init --project`.

Guild will prompt the before proceeding:

    >>> run("guild init --project sample-project", timeout=1)
    You are about to initialize a project in 'sample-project'
    Continue? (Y/n)
    <exit ...>

We can use `-y` to proceed without being prompted:

    >>> run("guild init --project sample-project -y")
    Initializing project in 'sample-project' using default template
    Copying ...
    Copying ...
    Updating sample-project/guild.yml
    <exit 0>
