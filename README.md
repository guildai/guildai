# Guild AI

[![CircleCI](https://circleci.com/gh/guildai/guild.svg?style=shield)](https://circleci.com/gh/guildai/guild)
[![PyPI version](https://badge.fury.io/py/guildai.svg)](https://badge.fury.io/py/guildai)

***Project status:*** beta

This is the active Guild source repository.

Guild has been rewritten in Python and has undergone substantial
changes since its original release.

Documentation on https://guild.ai will be forthcoming. For time being,
please submit issues to the [project GitHub issue
tracker](https://github.com/guildai/guild/issues).

## Installing Guild

Early releases of wheels for Linux and MacOS are available on PyPI. To
install the latest version, run:

```
$ pip install guildai --upgrade --pre
```

If your platform isn't support or you want to run from source, you can
compile Guild using the steps below.

## Compiling Guild from source

Clone Guild from GitHub:

    $ git clone https://github.com/guildai/guild

Build Guild:

    $ cd guild
    $ python setup.py build

You may alternatively run `make`.

If Guild builds successfully, run the `check` command with tests:

    $ guild/scripts/guild check --tests

You may alternatively run `make check`.

Please report any build errors or failed tests to the [project GitHub
issue tracker](https://github.com/guildai/guild/issues).

To run `guild` without typing its full path, create an alias:

```
alias guild=$GUILD_REPO/guild/scripts/guild
```

where `$GUILD_REPO` is a reference to your local Guild git repository.

You may alternatively install Guild in developer mode:

    $ python setup.py develop

NOTE: The above command may require that you run as a privileged user
(e.g. using `sudo`). To install Guild without elevated privelges, run
`python setup.py develop --user` and ensure that your local bin
directory (e.g. `~/.local/bin`) is in your shell path.

## Using Guild

Clone the Guild examples:

```
$ git clone https://github.com/guildai/examples guild-examples

```

Change to the `mnist2` example and train the default model:

```
$ cd guild-examples/mnist2
$ guild train
```

You will be asked to confirm that you want to train the `mnist-intro`
model. Press enter to continue.

Guild will train the MNIST intro model, which is a simple softmax
regression. It should only take a view seconds to train.

In a second terminal, change to the `mnist2` example directory and
start Guild View:

```
$ cd guild-examples/mnist2
$ guild tensorboard
```

This will open TensorBoard where you can view the runs for the
`mnist2` project.

## Getting help

Guild documentation is under development and not yet available. Use
the command line help to familiarize yourself with Guild's features.

<table>
<tr>
  <td><code>guild --help</td>
  <td>List available Guild commands</td>
</tr>
<tr>
  <td><code>guild COMMAND --help</td>
  <td>Show help for <code>COMMAND</code></td>
</tr>
</table>
