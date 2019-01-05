# Simplifying Guild

Even a basic Guild file can start to look complicated. Let's think
about ways to simplify it. This will also help articulate the salient
feature that gives Guild an identity.

Let's set aside the need to adapt an existing project. We can assume
green field for this discussion.

## Simplest of all - no Guild file

The simplest case for Guild is this:

    $ guild run train

This would look for `train.py` locally and run it.

We could retain the simple rule that arguments in the format
NAME=VALUE are passed to train as "--NAME VALUE".

So,

    $ guild run train learning-rate=0.01

This is close to something like this:

``` yaml
model: default
operations:
  train:
    main: train
    flags:
      learning-rate: 0.01
```

Even this simple snippet is arguably enough to put someone off the
tool.

Once you run this, you get a run - and all the nice features
associated with that run.

Backing up might be as simple as this:

    $ guild push --host pawnee --path ~/Runs

What about dependencies? Here's a common case:

    $ guild run train
    $ guild evaluate

There are dependencies across these operations:

- Files to download for train
- Trained model checkpoints to evaluate

It's simply not possible to support this without additional
information.

What's the simplest possible configuration for this (ignoring legacy
Guild file format)?

``` yml
train:
  requires:
    - http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz
    - http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz
    - http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz
    - http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz
```


## Notes on changes

- If top-level object is a map, assume this simplified format
  - model def is some default - maybe call this anonymous model?
  - keys are operations
