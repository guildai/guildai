# Args enhancements

## Background

Defining hyper parameters is an important topic. I glanced at some
models that had a lot hyper parameters (over 15).

At that point a researcher might not really want to have to define
argument for each of these. It might be a good idea, but researchers
are spending their mental energy on better ideas.

So we see stuff like this:

``` python
hypers = {'num_actors': 16,
          'rollout_length': 8,
          'env': 'dimChooserEnv-v0',  # 'angleEnv-v0',  # 'robotArmEnv-v0',  #
          'entropy_beta': 0.0,
          'critic_lambda': 0.5,
          'sc_critic_lambda': 0.5,
          'prediction_lambda': 0.1,
          'monotonic_lambda': 1.0,
          'discount': 0.99,
          'gae_lambda': 1.0,
          'hidden_layers': [256, 128, 64],
          'max_gradient_norm': None,
          'learning_rate': 0.01,
          'mode': 'saver',  # 'a2c',  #
          'K': 32,
          'huber': False,
          'number_of_pretrain_batches': 10000,
          'number_of_training_batches': 100000,
          'run_id': str(np.random.randint(1000))
}
```

These could just as easily be defined globally. Or they might be
defined using the [`param`](https://param.pyviz.org/) module.

The global equivalent might look like:

``` python
num_actors = 16
rollout_length = 8
env = 'dimChooserEnv-v0'  # 'angleEnv-v0',  # 'robotArmEnv-v0'
entropy_beta = 0.0
```

### Counter point

Here's the equivalent `hypers` support using argparse:

``` python
import argparse

p = argparse.ArgumentParser()
p.add_argument('--num_actors', default=16)
p.add_argument('--num_actors', default=16)
p.add_argument('--rollout_length', default=8)
p.add_argument('--env', default='dimChooserEnv-v0')
p.add_argument('--entropy_beta', default=0.0)
p.add_argument('--critic_lambda', default=0.5)
p.add_argument('--sc_critic_lambda', default=0.5)
p.add_argument('--prediction_lambda', default=0.1)
p.add_argument('--monotonic_lambda', default=1.0)
p.add_argument('--discount', default=0.99)
p.add_argument('--gae_lambda', default=1.0)
p.add_argument('--hidden_layers', default=[256, 128, 64])
p.add_argument('--max_gradient_norm', default=None)
p.add_argument('--learning_rate', default=0.01)
p.add_argument('--mode', default='saver')
p.add_argument('--K', default=32)
p.add_argument('--huber', default=False)
p.add_argument('--number_of_pretrain_batches', default=10000)
p.add_argument('--number_of_training_batches', default=100000)
p.add_argument('--run_id', default=str(np.random.randint(1000))
```

It's a little bit more work but now a lot.

## Current implementation

The flags scheme in Guild currently works with long-style
options. This is the convention used with most TensorFlow
examples. However, it has some drawbacks:

- Requires the use of argparse or TensorFlow flag support, which many
  researchers may not know or want to learn

- Researchers don't really care if anyone else uses their code, so
  stubbing out for command line changes to hyperparameters is not
  something they're likely to spend time on

- Using argparse is a duplication of effort if flags are also defined
  in the Guild file

## Alternative flag interface

We should use the existing flags scheme, but extend it to support
alternative flag interfaces.

Here's a simple model with a train operation and two hyperparameters:

``` yaml
model: test
operations:
  train:
    main: main
    flags-dest: main.params
    flags:
      epochs: null
      learning_rate: null
```

The `flags-dest` indicates that the flag values should be defined in
the global variable `params` in the `main` module. If `params` is a
dict, flag values will be set as dict items, otherwise Guild will
attempt to set the values as object attributes.

`flags-dest` might alternatively be `main` which would indicate that
the flag values should be defined as global variables.

By default Guild will pass flag values as command line arguments,
which is the current behavior.

We might name this `flags-config`, which is a general bucket for flag
related configuration.

``` yaml
flags-config:
  dest: main.params
```

## Externally defined flag values

The run command should support flags defined in external files.

I think the right interface is to use `@FILE` so that there's some
symmetry with other flag definitions.

For example:

    $ guild run train @params/train-1.json

Guild should support the formats: JSON, YAML, INI, CSV/TSV, and Python
modules.

We should support use of externally defined flag values that are
applied when a choice is specified.

``` yaml
model: test
operation:
  train:
    flags:
      epochs: null
      learning_rate: null
      profile:
        choices:
          p1:
            description: p1 profile foo
            args:
             - params/train-1.json
             - params/model-2.json
          p2:
            description: p2 profile bar
            args: params/train-2.json
        default: p1
```

## Duplication flag/arg definitions

A major problem for Guild, which is arguably more important to solve
than supporting alternative arg interfaces, is that Guild currently
requires that each flag by explicitly defined in the Guild file, while
at the same time, requiring that the project scripts use argparse to
parse command line arguments.

This is a barrier to adoption.

One approach might be to use an operation module to get help and use
that help to automatically support flags.

Something like this:

``` yaml
model: test
operations:
  train:
    main: train
    auto-flags: yes
```

When Guild sees auto-flags, it injects a workflow at the end of the
process of loading the file:

- Check the env cache for a flag definition corresponding to the md5
  hash of the main module source.

- If a valid cache definition exists, use it to define any undefined
  flags and any undefined flag attributes.

- If a valid cache definition does not exist, use the main module to
  generate help using config provided under the `auto-flags`
  attribute. By default, monkey patch argparse to capture arg
  definitions before loading the module and adjust `sys.argv` to
  include the `--help` option (or patch parse_args and circumvent the
  parsing and use the parser arguments, one per flag).

- Cache the definition if generated using the current md5 of the main
  module source. We can use cachecontrol to purge stale flag
  definitions as a matter of house keeping.

## Feedback from users

### Oliver Richter

- Happy to use argparse rather than globals or a global dict, so the
  idea of storing flag values in state directly is not that
  compelling.

- Wants to kick off a series of runs with a set of flag
  values. E.g. `guild run train learning-rate=[0.01,0.001,0.0001]
  discount=[0.95,0.99]` would start six runs. This ties into the
  tuning feature under consideration. This is a direct invocation of
  multi-run, which is maybe what we want to call this.

- Wants to specify a range for each flag for sampling and multi-run.

- Doesn't want to duplicate flag definitions in the Guild file.
