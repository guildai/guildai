---
doctest-type: bash
---

# DvC Example

This directory contains various examples of using DvC with Guild AI.

To run the examples, you must first install `dvc` with S3 support by
running `pip install dvc[s3]`.

## Supported Operations

Guild operations are defined in [`guild.yml`](guild.yaml).

    $ guild ops
    eval-models-dvc-dep        Use Guild to run the eval models operation
    eval-models-dvc-stage      Use Guild DvC plugin to run eval-models stage
    faketrain-dvc-stage        Use Guild DvC plugin to run faketrain stage
    hello-dvc-dep              Uses DvC dependency to fetch required file if needed
    hello-dvc-dep-always-pull  Uses DvC dependency to always fetch required file
    hello-dvc-stage            Uses Guild DvC plugin to run hello stage
    hello-guild-op             Standard Guild dependency example without DvC support
    prepare-data-dvc-dep       Use DvC dependency to fetch required file if needed
    prepare-data-dvc-stage     Use Guild DvC plugin to run prepare-data stage
    train-models-dvc-dep       Use Guild to run the train models operation
    train-models-dvc-stage     Use Guild DvC plugin to run train-models stage

Guild also supports the DvC stages defined in [`dvc.yaml`](dvc.yaml).

## Simple Hello

The 'hello' operations illustrate various DvC integration features in
Guild. These operations all run the [`hello.py`](hello.py) script, which relies on
a file named `hello.in` to print a message.

    $ cat hello.py
    msg = "Hello %s!" % open("hello.in").read().strip()
    print(msg)
    with open("hello.out", "w") as f:
        f.write("%s\n" % msg)

### Non DvC implementation of hello

The 'hello-guild-op' uses Guild's built-in `file` resource type to
resolve the dependency on `hello.in`. As `hello.in` doesn't exist in
the project, the operation fails with a message instructing the user
to run `dvc pull` to first get the file.

    $ guild run hello-guild-op -y
    Resolving file:hello.in dependency
    guild: run failed because a dependency was not met: could not resolve
    'file:hello.in' in file:hello.in resource: cannot find source file 'hello.in'
    Missing hello.in - run 'dvc pull hello.in' to fetch it
    <exit 1>

This scheme can be improved using the `dvcfile` source type. This uses
DvC to fetch a file from a cache or remote if it's not available.

    $ guild run hello-dvc-dep -y
    Resolving dvcfile:hello.in dependency
    Fetching DvC resource hello.in
    A       hello.in
    1 file added and 1 file fetched
    Hello World!

## DvC Params and Metrics

Guild lets you set DvC stage params as flag values. It also logs DvC
metrics at the end of the run. The 'faketrain-dvc-stage' operation
illustrates this. It uses the module `guild.plugins.dvc_stage_main` to
run the 'faketrain' stage defined in `dvc.yaml`.

Because DvC params are exposed as Guild flags, you can run batches of
DvC stages this way:

    $ guild run faketrain-dvc-stage x=[-1.0,0.0,1.0] -y
    INFO: [guild] Running trial ...: faketrain-dvc-stage (noise=0.1, x=-1.0)
    INFO: [guild] Resolving config:params.json.in dependency
    INFO: [guild] Initializing run
    INFO: [guild] Copying faketrain.py
    INFO: [guild] Running stage 'faketrain'
    x: -1.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] Logging metrics from summary.json
    INFO: [guild] Running trial ...: faketrain-dvc-stage (noise=0.1, x=0.0)
    INFO: [guild] Resolving config:params.json.in dependency
    INFO: [guild] Initializing run
    INFO: [guild] Copying faketrain.py
    INFO: [guild] Running stage 'faketrain'
    x: 0.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] Logging metrics from summary.json
    INFO: [guild] Running trial ...: faketrain-dvc-stage (noise=0.1, x=1.0)
    INFO: [guild] Resolving config:params.json.in dependency
    INFO: [guild] Initializing run
    INFO: [guild] Copying faketrain.py
    INFO: [guild] Running stage 'faketrain'
    x: 1.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] Logging metrics from summary.json

Guild reads `summary.json`, which is defined as the metrics output
file for the stage. It logs the results as scalar summaries, which can
be viewd in Guild as well as TensorBoard.

    $ guild compare -t -n3 -cc .operation,=x,loss
    run  operation            x     loss
    ...  faketrain-dvc-stage  1.0   ...
    ...  faketrain-dvc-stage  0.0   ...
    ...  faketrain-dvc-stage  -1.0  ...

## Run DvC stage directly

Guild supports running a DvC stage directly in the format
`dvc.yaml:<stage>`.

Let's run the DvC pipeline defined in `dvc.yaml`. Note that Guild does
not automatically run upstream stage dependencies the way DvC
does. You must explicitly run required stages.

For example, if we run the `train-models` stage, we get an error.

    $ guild run dvc.yaml:train-models -y
    WARNING: cannot find a suitable run for required resource
    'dvcstage:prepare-data'
    Resolving dvcfile:train_models.py dependency
    Resolving dvcstage:prepare-data dependency
    guild: run failed because a dependency was not met: could not resolve
    'dvcstage:prepare-data' in dvcstage:prepare-data resource: no suitable
    run for 'prepare-data' stage
    <exit 1>

Let's run the three pipeline operations in order.

### Prepare data

Run the stage:

    $ guild run dvc.yaml:prepare-data -y
    Resolving dvcfile:iris.csv dependency
    Resolving dvcfile:prepare_data.py dependency
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'prepare-data'
    Saving iris.npy

List run files:

    $ guild ls -n
    dvc.lock
    dvc.yaml
    iris.csv
    iris.npy
    prepare_data.py

Note that the run directory contains only the input and output files
and not the project source code. This is consistent with the way Guild
runs other operations. Source code is separated from the files being
operated on.

    $ guild ls -n --sourcecode  # doctest: +REPORT_UDIFF
    README.md
    data_util.py
    dvc.config.in
    dvc.yaml
    eval_models.py
    faketrain.py
    guild.yml
    hello.in.dvc
    hello.py
    iris.csv
    iris.csv.dvc
    models-eval.json
    params.json.in
    prepare_data.py
    requirements.txt
    setup.py
    summary.json
    train_models.py

### Train models

Run the stage:

    $ guild run dvc.yaml:train-models train.C=2.0 -y
    Resolving dvcfile:train_models.py dependency
    Resolving dvcstage:prepare-data dependency
    Using run ... for dvcstage:prepare-data resource
    Resolving config:params.json.in dependency
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'train-models'
    C=2.000000
    gamma=0.700000
    max_iters=10000.000000
    Saving model-1.joblib
    Saving model-2.joblib
    Saving model-3.joblib
    Saving model-4.joblib

Show run info, including the flags:

    $ guild runs info
    id: ...
    operation: dvc.yaml:train-models
    ...
    dvc-stage: train-models
    ...
    flags:
      dvcstage:prepare-data: ...
      train.C: 2.0
      train.gamma: 0.7
      train.max-iters: 10000
    scalars:

List run files:

    $ guild ls -n
    dvc.lock
    dvc.yaml
    iris.npy
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    params.json.in
    train_models.py

### Evaluate the models

Run the stage:

    $ guild run dvc.yaml:eval-models eval.plot-spacing=0.8 -y
    Resolving dvcfile:eval_models.py dependency
    Resolving dvcstage:prepare-data dependency
    Using run ... for dvcstage:prepare-data resource
    Resolving dvcstage:train-models dependency
    Using run ... for dvcstage:train-models resource
    Resolving config:params.json.in dependency
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'eval-models'
    plot_spacing=0.800000
    Saving models-eval.json
    Saving models-eval.png
    INFO: [guild] Logging metrics from models-eval.json

Show run info, including flags and metrics/scalars:

    $ guild runs info
    id: ...
    operation: dvc.yaml:eval-models
    ...
    dvc-stage: eval-models
    ...
    flags:
      dvcstage:prepare-data: ...
      dvcstage:train-models: ...
      eval.plot-spacing: 0.8
    scalars:
      modle-1-score: ... (step 0)
      modle-2-score: ... (step 0)
      modle-3-score: ... (step 0)
      modle-4-score: ... (step 0)

List run files:

    $ guild ls -n
    dvc.lock
    dvc.yaml
    eval_models.py
    events.out.tfevents...
    iris.npy
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    models-eval.json
    models-eval.png
    params.json.in

Note the `events.out.tfevents*` file that Guild creates. This contains
the metrics generated by the stage as TF scalar summaries. This is the
format used by Guild and TensorBoard, letting DvC stages participate
in the Guild/TensorBoard tooling ecosystem.
