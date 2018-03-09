# Default project info

This test assumes a sample project has been initialized:

    >>> run("find sample-project | sort")
    sample-project
    sample-project/guild.yml
    sample-project/train.py
    <exit 0>

We can list the project models:

    >>> run("guild -C sample-project models")
    Limiting models to 'sample-project' (use --all to include all)
    ./sample-project/sample-project  TODO - model description
    <exit 0>

And operations:

    >>> run("guild -C sample-project operations")
    Limiting models to 'sample-project' (use --all to include all)
    ./sample-project/sample-project:train  Train the model
    <exit 0>
