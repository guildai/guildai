# Check before init

This test assumes that Guild is installed and TensorFlow is not
installed.

Running check without TensorFlow installed will result in an error:

    >>> run("guild check")
    guild_version:             ...
    guild_home:                ...
    guild_install_location:    ...
    installed_plugins:         cloudml, cpu, disk, gpu, keras, memory
    python_version:            ...
    tensorflow_version:        NOT INSTALLED (No module named '...')
    nvidia_smi_version:        ...
    guild: there are problems with your setup
    Refer to the issues above for more information or rerun check with the --verbose option.
    <exit 1>

We also expect there to be no Guild environment files:

    >>> run("cd $WORKSPACE && find .guild")
    .guild
    <exit 0>
