# Reinit sample project

This tests illustrates Guild's behavior when attempting to initialize
a project that's already been initialized.

We're assuming `sample-project` has been initialized:

    >>> run("find sample-project | sort")
    sample-project
    sample-project/guild.yml
    sample-project/train.py
    <exit 0>

We get an error when we try to initialize the project again:

    >>> run("guild init --project sample-project -y")
    Initializing project in 'sample-project' using default template
    guild: sample-project/... exists and would be overwritten
    <exit 1>
