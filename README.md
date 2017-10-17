# Guild Python

***Project status:*** pre-alpha

This is the active Guild source repository.

Guild has been rewritten in Python and has undergone substantial
changes since its original release.

Documentation on https://guild.ai will be forthcoming. For time being,
please submit issues to the [project GitHub issue
tracker](https://github.com/guildai/guild-python/issues).

## Installing Guild AI

Preliminary releases of Linux wheels are available on PyPI. To install
the latest version, run:

```
$ pip install tensorflow
```
```
$ pip install psutil
```
```
$ pip install guildai --upgrade
```

If your platform isn't support, you can compile Guild AI from source
(see steps below).

## Compiling Guild AI from source

Guild Python requires Bazel 0.5.4 or higher to build. See [Installing
Bazel](https://docs.bazel.build/versions/master/install.html) for help
with you system.

Clone Guild Python from GitHub:

    $ git clone https://github.com/guildai/guild-python.git

Build Guild Python using the `bazel` command:

    $ cd guild-python
    $ bazel build guild

You may alternatively simply run `make`.

The initial Guild Python build will take some time as Bazel will
download several dependencies, including TensorBoard. Subsequent
builds will run faster.

If Guild Python builds successfully, run the `check` command with
tests:

    $ bazel-bin/guild/guild check --tests

You may alternatively run `make check`.

Please report any failed tests to the [project GitHub issue
tracker](https://github.com/guildai/guild-python/issues).

To run `guild` without typing its full path, create an alias:

```
alias guild=$GUILD_REPO/bazel-bin/guild/guild
```

where `$GUILD_REPO` is a reference to your local Guild git repository.

## Using Guild AI

Clone the Guild Examples:

```
$ git clone https://github.com/guildai/guild-examples.git

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
$ guild view
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
