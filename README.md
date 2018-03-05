# Guild AI

[![CircleCI](https://circleci.com/gh/guildai/guild.svg?style=shield)](https://circleci.com/gh/guildai/guild)
[![PyPI version](https://badge.fury.io/py/guildai.svg)](https://badge.fury.io/py/guildai)

This is the source repository for Guild AI.

Guild AI is a Python application released under the Apache 2 open
source license that streamlines TensorFlow and Keras deep learning
development.

- **Latest release on PyPI** - [https://pypi.python.org/pypi/guildai](https://pypi.python.org/pypi/guildai)
- **Guild AI website** - [https://www.guild.ai](https://www.guild.ai)
- **Documentation** - [https://www.guild.ai/docs](https://www.guild.ai/docs/)
- **Open issues** - [https://github.com/guildai/guild/issues](https://github.com/guildai/guild/issues)

## Quick start

The steps below will install Guild AI, train a simple model, and view
the results. For detailed installation instructions, see
[https://www.guild.ai/install/](https://www.guild.ai/install/).

Run each step below at a command line. Omit the '$' character when
executing a command.

**Step 1. Install Guild AI using pip**

```
$ pip install guildai --upgrade
```

**Step 2. Verify your installation**

```
$ guild check
```

**Step 3. Install a model package**

```
$ guild install mnist
```

**Step 4. Train a model**

```
$ guild train softmax
```

**Step 5. View the training run**

```
$ guild view
```

## Learning more

Refer to [https://www.guild.ai](https://www.guild.ai) for complete
coverage of Guild AI.

If you have questions or are facing problems, please open an issue at
[https://github.com/guildai/guild/issues](https://github.com/guildai/guild/issues).
