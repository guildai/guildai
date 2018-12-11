# Hyperparameter Tuning

Without this facility, Guild is just a toy. No one runs experiments
manually - they script them.

## Ray

I think the approach to hyperparameter tuning should be to simply work
with Ray and Tune until we see something working.

Use Ray Tune with grid search and try optimizing the Fashion MNIST
example on a laptop to start. Then incrementally move to more
interesting scenarios:

- 1 Run an image classifier with a larger network (e.g. ResNet-50)
  - 1.1 Single GPU server (e.g. pawnee)
  - 1.2 Multi-GPU server (local and EC2)
  - 1.3 Two single GPU servers (EC2)
  - 1.4 Two multi-GPU servers (EC2)

The next scenario might be to include a second operation so that the
optimization is maximizing validation accuracy.

Once some of this is working, look to cleanup the
implementation. Maybe this is a package. Maybe it's a remote
implementation. Not sure.

I think get Will involved to vet this work. Also, any other early
adopter.

### Maybe use a package

Maybe start with just getting things working with a project level
helper. In fact, maybe this is a package: `gpkg.ray` and there's a
utility operation.

``` yaml
model: test
operations:
  tune:
    main: gpkg.ray/tuner:tune
    flags:
      cluster:
        description: Ray cluster to tune on
        default: ray
        required: yes
    config:
      steps:
        - train
        - evaluate
      optimize:
        - max: acc_val
```

This could be the approach we take to experiment with this support.

A Ray cluster could be defined this way:

``` yaml
remotes:
  geronimo:
    type: ray-cluster

  crazyhorse:
    type: remotes-cluster
    remotes:
      - pawnee-1
      - pawnee-2
```

I think the first pass though is to just get this running in one way
or another.
