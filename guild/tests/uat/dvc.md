---
doctest: -PY37
---

# DvC support

These tests make use of the `dvc` example. This project is used as a
template for a working DvC repo.

Create a project directory. This is where we'll setup the project.

    >>> project_dir = mkdtemp()

Run `setup.py` from the `dvc` example directory to setup the project.

    >>> cd(example("dvc"))

    >>> run("python setup.py '%s'" % project_dir)
    Initializing ...
    Initializing Git
    Initializing DvC
    Copying source code files

Use the project for the remaining tests.

    >>> use_project(project_dir)

The project conists of a Git repo, a DvC repo, and the project files
themselves.

    >>> find(".")
    .dvc/.gitignore
    .dvc/config
    .dvc/tmp/hashes/local/cache.db
    .dvc/tmp/links/cache.db
    .dvcignore
    .git/...
    README.md
    data_util.py
    dvc.config.in
    dvc.yaml
    eval_models.py
    faketrain.py
    guild.yml
    hello.in.dvc
    hello.py
    iris.csv.dvc
    params.json.in
    prepare_data.py
    requirements.txt
    setup.py
    train_models.py

The project defines several operations in `guild.yml`.

    >>> run("guild ops")  # doctest: +REPORT_UDIFF
    eval-models-dvc-dep        Use Guild to run the eval models operation
    eval-models-dvc-stage      Use Guild DvC plugin to run eval-models stage
    faketrain-dvc-stage        Use Guild DvC plugin to run faketrain stage
    hello-dvc-dep              Uses DvC dependency to fetch required file if needed
    hello-dvc-dep-2            Resolves two DvC file dependencies
    hello-dvc-dep-always-pull  Uses DvC dependency to always fetch required file
    hello-dvc-stage            Uses Guild DvC plugin to run hello stage
    hello-guild-op             Standard Guild dependency example without DvC support
    prepare-data-dvc-dep       Use DvC dependency to fetch required file if needed
    prepare-data-dvc-stage     Use Guild DvC plugin to run prepare-data stage
    train-models-dvc-dep       Use Guild to run the train models operation
    train-models-dvc-stage     Use Guild DvC plugin to run train-models stage

DvC-enabled projects use `dvc.yaml` to define DvC stages, among other
things.

    >>> dvc_config = yaml.safe_load(open("dvc.yaml"))

## DvC resource sources

The dvc plugin supports a `dvcfile` source type. This is used in the
sample project's `hello-dvc-dep` operation.

    >>> gf = guildfile.for_dir(".")
    >>> opdef = gf.default_model.get_operation("hello-dvc-dep")
    >>> opdef.dependencies
    [<guild.guildfile.OpDependencyDef dvcfile:hello.in>]

The `dvcfile` source type acts like a `file` source when the specified
file is available in the project. If the file isn't available, Guild
uses `dvc pull` to fetch it.

Confirm that `hello.in` does not exist in the project.

    >>> exists("hello.in")
    False

Run the operation.

    >>> run("guild run hello-dvc-dep -y")
    Resolving dvcfile:hello.in
    Fetching DvC resource hello.in
    A       hello.in
    1 file added and 1 file fetched
    Hello World!

Guild uses DvC to retrieve the project from its repository.

The run manifest shows the source code and resolved dependencies.

    >>> run("guild cat -p .guild/manifest")  # doctest: +REPORT_UDIFF
    s .dvcignore 158bdf3e9a5f1cc532c6675e8079bd2eeabe9d18 .dvcignore
    s README.md b26978be007169badc45070b27a6bfd3b2440da2 README.md
    s data_util.py 7f25fc56a155212abdffec82fdf63a723144ff74 data_util.py
    s dvc.config.in 3ef04083edec4c15909f60aea3f685e5551f5b69 dvc.config.in
    s dvc.yaml 915c778af8ee728754c7196a565a495b00bda1d9 dvc.yaml
    s eval_models.py b579028cfecf6410b7d9a8d9c81d9bf112d2e7a8 eval_models.py
    s faketrain.py ac665f1c42be6e5096c30d7b588a8cbfedd55891 faketrain.py
    s guild.yml 3387c13e7a59764599ddc9f960df3a15b49e6b00 guild.yml
    s hello.in.dvc 34fc482704b5d6e14520b1176fe78d841f94f111 hello.in.dvc
    s hello.py e02f0f99ee58b5e4cc1dc55fc5a5fbd2f1dc1a17 hello.py
    s iris.csv.dvc e3c585206b17f4af6643d631597041229130dfb7 iris.csv.dvc
    s params.json.in 4f3b452fd0e8ab0a8cecb8cb5560effc7f8d25de params.json.in
    s prepare_data.py 57ccaa3725415e99ec0b3d8323c060a73b3417bf prepare_data.py
    s requirements.txt bd2d0f656b9bf3b9a94a8670b5b3763274dd97f3 requirements.txt
    s setup.py 7332d32ccbbbc302f47e7cbfa892d7e6ce1887cd setup.py
    s train_models.py f6e97ad8827262c41cc94944ffd560a4a2ab399f train_models.py
    s .dvc/config 3ef04083edec4c15909f60aea3f685e5551f5b69 .dvc/config
    i .dvc/.gitignore da39a3ee5e6b4b0d3255bfef95601890afd80709 dvcfile:hello.in
    i .dvc/cache - dvcfile:hello.in
    i .dvc/tmp - dvcfile:hello.in
    i .git - dvcfile:hello.in
    d hello.in 418f1bfdf3ebb0091021656d8ed6d611b3ae6222 dvcfile:hello.in

The list of run files contains the source code files and `hello.in`.

    >>> run("guild ls -n")
    README.md
    data_util.py
    dvc.config.in
    dvc.yaml
    eval_models.py
    faketrain.py
    guild.yml
    hello.in
    hello.in.dvc
    hello.out
    hello.py
    iris.csv.dvc
    params.json.in
    prepare_data.py
    requirements.txt
    setup.py
    train_models.py

Show only dependencies using the `--dependencies` flag.

    >>> run("guild ls -n --dependencies")
    hello.in

Generated files include the file generated by the operation
`hello.out`.

    >>> run("guild ls -n --generated")
    hello.out

The resolved version of 'hello.in' is from the DvC repository.

    >>> run("guild cat -p hello.in")
    World

The project does not contain 'hello.in'.

    >>> exists("hello.in")
    False

We can modify the project file, in which case the modified version is
used when resolving the dependency.

    >>> write("hello.in", "Project")

    >>> run("guild run hello-dvc-dep -y")
    Resolving dvcfile:hello.in
    Hello Project!

This behavior is identical to that of a normal `file` source
resolution.

    >>> run("guild cat -p .guild/manifest")
    ???
    d hello.in f6f4da8d93e88a08220e03b7810451d3ba540a34 file:hello.in

Note that the dependency is resolved as a `file` type.

### Configuring DvC

DvC configuration for a project is providfed using
`dvc.config.in`. Guild uses this to generate run-specific
configuration. This is where we configure remote storage.

    >>> cat("dvc.config.in")
    [core]
        analytics = false
        remote = guild-pub
    ['remote "guild-pub"']
        url = https://guild-pub.s3.amazonaws.com/dvc-store
    ['remote "guild-s3"']
        url = s3://guild-pub/dvc-store

Run-specific configuration is generated as `.dvc/config`.

    >>> run("guild cat -p .dvc/config")
    [core]
        analytics = false
        remote = guild-pub
    ['remote "guild-pub"']
        url = https://guild-pub.s3.amazonaws.com/dvc-store
    ['remote "guild-s3"']
        url = s3://guild-pub/dvc-store
    <exit 0>

A DvC dependency can always be pulled by setting 'always-pull' to true
in the Guild file. The operation `hello-dvc-dep-always-pull`
illustrates this.

The project contains a modified version of 'hello.in'.

    >>> cat("hello.in")
    Project

Run `hello-dvc-dep-alwats-pull`.

    >>> run("guild run hello-dvc-dep-always-pull -y")
    Resolving dvcfile:hello.in
    Fetching DvC resource hello.in
    A       hello.in
    1 file added and 1 file fetched
    Hello World!
    <exit 0>

    >>> run("guild ls -n --dependencies")
    hello.in

The resolved dependency is from the remote storage, not the project.

    >>> run("guild cat -p hello.in")
    World

## Use of `guild.plugins.dvc_stage_main`

The module `guild.plugins.dvc_stage_main` can be used to run a stage
defined in dvc.yaml.

These operations use this module as their `main` attr:

- `prepare-data-dvc-stage`
- `train-models-dvc-stage`
- `eval-models-dvc-stage`

    >>> run("guild run prepare-data-dvc-stage --print-cmd")
    ??? -um guild.op_main guild.plugins.dvc_stage_main prepare-data --

    >>> run("guild run train-models-dvc-stage --print-cmd")
    ??? -um guild.op_main guild.plugins.dvc_stage_main train-models --

    >>> run("guild run eval-models-dvc-stage --print-cmd")
    ??? -um guild.op_main guild.plugins.dvc_stage_main eval-models --

Guild handles dependency resolution from this module as follows:

- Dependencies that are resolved from the project are copied from the
  project dir (if present) or pulled using the DvC config file for the
  dependency.

- Dependencies that are generated by upstream stages are resolved by
  looking for Guild operations for those stages. Such operation are
  designated by a `dvc-stage` run attribute matching the upstream
  stage name.

DvC stages are defined in `dvc.yaml` in the project.

    >>> cat("dvc.yaml")  # doctest: +REPORT_UDIFF
    stages:
      prepare-data:
        cmd: python prepare_data.py
        deps:
        - iris.csv
        - prepare_data.py
        outs:
        - iris.npy
      faketrain:
        cmd: python faketrain.py
        params:
          - params.json.in:
              - x
        deps:
        - faketrain.py
        metrics:
        - summary.json:
            cache: false
      train-models:
        cmd: python train_models.py
        params:
          - params.json.in:
              - train.C
              - train.gamma
              - train.max-iters
        deps:
        - iris.npy
        - train_models.py
        outs:
        - model-1.joblib
        - model-2.joblib
        - model-3.joblib
        - model-4.joblib
      eval-models:
        cmd: python eval_models.py
        params:
          - params.json.in:
              - eval.plot-spacing
        deps:
        - iris.npy
        - model-1.joblib
        - model-2.joblib
        - model-3.joblib
        - model-4.joblib
        - eval_models.py
        metrics:
        - models-eval.json:
            cache: false
        outs:
        - models-eval.png
      hello:
        deps:
        - hello.in
        - hello.py
        cmd: python hello.py
        outs:
        - hello.out

As specified in `dvc.yaml`, `train-models-dvc-stage` requires
`iris.npy`, which is provided by the `prepare-data` DvC stage. This
information is not configured in `guild.yml` - Guild uses DvC for
dependency configuration.

Try to run `train-models-dvc-stage`.

    >>> run("guild run train-models-dvc-stage -y")
    INFO: [guild] Initializing run
    guild: no suitable run for stage 'prepare-data' (needed for iris.npy)
    <exit 1>

Similarly, try to run `eval-models-dvc-stage`.

    >>> run("guild run eval-models-dvc-stage -y")
    INFO: [guild] Initializing run
    guild: no suitable run for stage 'prepare-data' (needed for iris.npy)
    <exit 1>

To run these downstream operations, we need to first satisfy the
upstream requirements.

Run `prepare-data-dvc-stage`.

    >>> run("guild run prepare-data-dvc-stage -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Initializing run
    INFO: [guild] Fetching iris.csv
    INFO: [guild] Fetching DvC resource iris.csv
    A       iris.csv
    1 file added and 1 file fetched
    INFO: [guild] Running stage 'prepare-data'
    Saving iris.npy
    <exit 0>

This resolves `iris.csv` by pulling from remote storage. This is
reflected as a resolved dependency file.

    >>> run("guild ls -n --dependencies")
    iris.csv

NOTE, however, the `deps` attribute is missing any formal dependency
spec. This SHOULD be implemented by the DvC plugin.

    >>> run("guild select --attr deps")
    {}

The operation generates `iris.npy`.

    >>> run("guild ls -n --generated")
    iris.npy

With a `prepare-data` run, we can run `train-models`.

    >>> run("guild run train-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Initializing run
    INFO: [guild] Using ... for 'prepare-data' DvC stage dependency
    INFO: [guild] Linking iris.npy
    INFO: [guild] Running stage 'train-models'
    C=1.000000
    gamma=0.700000
    max_iters=10000.000000
    Saving model-1.joblib
    Saving model-2.joblib
    Saving model-3.joblib
    Saving model-4.joblib
    <exit 0>

The run files:

    >>> run("guild ls -n")  # doctest: +REPORT_UDIFF
    README.md
    data_util.py
    dvc.config.in
    dvc.lock
    dvc.yaml
    eval_models.py
    faketrain.py
    guild.yml
    hello.in.dvc
    hello.py
    iris.csv.dvc
    iris.npy
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    params.json.in
    prepare_data.py
    requirements.txt
    setup.py
    train_models.py
    <exit 0>

Dependencies:

    >>> run("guild ls -nd")
    iris.npy

Generated files:

    >>> run("guild ls -ng")
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib

And with `train-models` and `prepare-data` we can run `eval-models`.

    >>> run("guild run eval-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Initializing run
    INFO: [guild] Using ... for 'prepare-data' DvC stage dependency
    INFO: [guild] Linking iris.npy
    INFO: [guild] Using ... for 'train-models' DvC stage dependency
    INFO: [guild] Linking model-1.joblib
    INFO: [guild] Linking model-2.joblib
    INFO: [guild] Linking model-3.joblib
    INFO: [guild] Linking model-4.joblib
    INFO: [guild] Running stage 'eval-models'
    plot_spacing=0.400000
    Saving models-eval.json
    Saving models-eval.png
    INFO: [guild] Logging metrics from models-eval.json
    <exit 0>

    >>> run("guild ls -n")  # doctest: +REPORT_UDIFF
    README.md
    data_util.py
    dvc.config.in
    dvc.lock
    dvc.yaml
    eval_models.py
    events.out.tfevents...
    faketrain.py
    guild.yml
    hello.in.dvc
    hello.py
    iris.csv.dvc
    iris.npy
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    models-eval.json
    models-eval.png
    params.json.in
    prepare_data.py
    requirements.txt
    setup.py
    train_models.py

Dependencies:

    >>> run("guild ls -nd")
    iris.npy
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib

Generated files:

    >>> run("guild ls -ng")
    events.out.tfevents...
    models-eval.json
    models-eval.png

### Logging summaries from metrics

After a DvC stage is run, Guild reads any metrics generated by the
stage and logs the values as TF summaries.

The eval operation writes metrics to 'models-eval.json'. This is
defined in 'dvc.yaml'.

    >>> run("guild cat -p dvc.yaml")
    stages:
      ...
      eval-models:
        ...
        metrics:
        - models-eval.json:
            cache: false
        ...
    <exit 0>

    >>> run("guild cat -p models-eval.json")
    {"modle-1-score": 0.82,
     "modle-2-score": 0.8,
     "modle-3-score": 0.826...,
     "modle-4-score": 0.813...}

Guild reads the values and writes them summaries.

    >>> run("guild runs info")
    id: ...
    operation: eval-models-dvc-stage
    ...
    scalars:
      modle-1-score: 0.820000 (step 0)
      modle-2-score: 0.800000 (step 0)
      modle-3-score: 0.826... (step 0)
      modle-4-score: 0.813... (step 0)
    <exit 0>

## Guild simulated stage with param flags

The operation `train-models-dvc-dep` uses a standard Guild operation
without DvC to run the training operation. It uses `params.json.in`
for the args dest, which is is consistent with the DvC use of
params. It defines a dependency on the DvC stage `prepare-data` using
the `dvcstage` source type.

    >>> run("guild run train-models-dvc-dep train.C=2.0 -y")  # doctest: +REPORT_UDIFF
    Resolving config:params.json.in
    Resolving dvcstage:prepare-data
    Using run ... for dvcstage:prepare-data
    C=2.000000
    gamma=0.700000
    max_iters=10000.000000
    Saving model-1.joblib
    Saving model-2.joblib
    Saving model-3.joblib
    Saving model-4.joblib
    <exit 0>

    >>> run("guild ls -nd")
    iris.npy
    params.json

    >>> run("guild ls -ng")
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib

## Batches with a DvC stage

The 'faketrain' DvC stage can be run using the 'faketrain-dvc-stage'
operation. We can use the flag support to run a batch.

    >>> run("guild run faketrain-dvc-stage x=[-1.0,0.0,1.0] -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Running trial ...: faketrain-dvc-stage (noise=0.1, x=-1.0)
    INFO: [guild] Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'faketrain'
    x: -1.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] Logging metrics from summary.json
    INFO: [guild] Running trial ...: faketrain-dvc-stage (noise=0.1, x=0.0)
    INFO: [guild] Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'faketrain'
    x: 0.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] Logging metrics from summary.json
    INFO: [guild] Running trial ...: faketrain-dvc-stage (noise=0.1, x=1.0)
    INFO: [guild] Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'faketrain'
    x: 1.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] Logging metrics from summary.json

    >>> run("guild compare -t -cc .operation,.status,.label,=noise,=x,loss -n3")
    run  operation            status     label             noise  x     loss
    ...  faketrain-dvc-stage  completed  noise=0.1 x=1.0   0.1    1.0   ...
    ...  faketrain-dvc-stage  completed  noise=0.1 x=0.0   0.1    0.0   ...
    ...  faketrain-dvc-stage  completed  noise=0.1 x=-1.0  0.1    -1.0  ...

## Cross op-style dependencies

There are two operation styles in the `dvc` sample project:

- Standard Guild that provide the same functionality as DvC stages
- Wrapped DvC stages

It's possible for a standard Guild operation (non-wrapped DvC op) to
provide a DvC stage by writing a 'dvc:stage' run attribute with the
applicable stage name.

Reset the project environment.

    >>> use_project(project_dir)

When we run a downstream train DvC stage, it fails because we don't
have prepared data.

    >>> run("guild run train-models-dvc-stage -y")
    INFO: [guild] Initializing run
    guild: no suitable run for stage 'prepare-data' (needed for iris.npy)
    <exit 1>

We can satisfy this requirement using a non-DvC operation that
provides the required prepared data. It uses a `dvcfile` dependency
but does not run as a DvC stage.

    >>> run("guild run prepare-data-dvc-dep -y")
    Resolving dvcfile:iris.csv
    Fetching DvC resource iris.csv
    A       iris.csv
    1 file added and 1 file fetched
    Saving iris.npy
    <exit 0>

    >>> run("guild ls -nd")
    iris.csv

The operation generates `iris.npy`.

    >>> run("guild ls -ng")
    iris.npy

This operation writes a 'dvc:stage' attribute that indicates that the
run provides the output files for the 'prepare-data' stage.

    >>> run("guild runs info")
    id: ...
    operation: prepare-data-dvc-dep
    ...
    dvc-stage: prepare-data
    ...
    <exit 0>

The DvC train stage can use this run to satisfy its dependency.

    >>> run("guild run train-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Initializing run
    INFO: [guild] Using ... for 'prepare-data' DvC stage dependency
    INFO: [guild] Linking iris.npy
    INFO: [guild] Running stage 'train-models'
    C=1.000000
    gamma=0.700000
    max_iters=10000.000000
    Saving model-1.joblib
    Saving model-2.joblib
    Saving model-3.joblib
    Saving model-4.joblib
    <exit 0>

## Run DvC stage directly

Guild supports running a stage defined in dvc.yaml directly using the
operation name syntax `dvc.yaml:<stage>`.

Here's the op help for the `faketrain` stage.

    >>> run("guild run dvc.yaml:faketrain --help-op")
    Usage: guild run [OPTIONS] dvc.yaml:faketrain [FLAG]...
    <BLANKLINE>
    Stage 'faketrain' imported from dvc.yaml
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      x  (default is 0.1)
    <exit 0>

Note that Guild imports the required stage params as flags.

We can run the stage as an operation, including as a batch.

    >>> run("guild run dvc.yaml:faketrain x=[0.2,0.3] -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Running trial ...: dvc.yaml:faketrain (x=0.2)
    INFO: [guild] Resolving dvcfile:faketrain.py
    INFO: [guild] Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'faketrain'
    x: 0.200000
    noise: 0.100000
    loss: ...
    INFO: [guild] Running trial ...: dvc.yaml:faketrain (x=0.3)
    INFO: [guild] Resolving dvcfile:faketrain.py
    INFO: [guild] Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'faketrain'
    x: 0.300000
    noise: 0.100000
    loss: ...
    <exit 0>

When run directly, the run has a `dvc-stage` attribute, which
specifies the stage.

    >>> run("guild runs info")
    id: ...
    operation: dvc.yaml:faketrain
    ...
    dvc-stage: faketrain
    tags:
    flags:
      x: 0.3
    scalars:
      loss: ... (step 0)
      noise: ... (step 0)
    <exit 0>

### Dependencies

When run directly, Guild sets up dependencies between stage
operations. These are used to resolve required files from upstream
operations/stages.

Reset the project environment.

    >>> use_project(project_dir)

Try to run the train stage, which depends on prepare data.

    >>> run("guild run dvc.yaml:train-models -y")
    WARNING: cannot find a suitable run for required resource 'dvcstage:prepare-data'
    Resolving dvcfile:train_models.py
    Resolving dvcstage:prepare-data
    guild: run failed because a dependency was not met: could not resolve
    'dvcstage:prepare-data' in dvcstage:prepare-data resource: no suitable
    run for 'prepare-data' stage
    <exit 1>

The run failed.

    >>> run("guild runs info")
    id: ...
    operation: dvc.yaml:train-models
    from: .../dvc.yaml
    status: error
    ...
    <exit 0>

Run the required prepare data stage.

    >>> run("guild run dvc.yaml:prepare-data -y")
    Resolving dvcfile:iris.csv
    Fetching DvC resource iris.csv
    A       iris.csv
    1 file added and 1 file fetched
    Resolving dvcfile:prepare_data.py
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'prepare-data'
    Saving iris.npy
    <exit 0>

This generates the files required by the train operation.

    >>> run("guild ls -ng")
    iris.npy

Run the train stage again.

    >>> run("guild run dvc.yaml:train-models -y")  # doctest: +REPORT_UDIFF
    Resolving dvcfile:train_models.py
    Resolving dvcstage:prepare-data
    Using run ... for dvcstage:prepare-data
    Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'train-models'
    C=1.000000
    gamma=0.700000
    max_iters=10000.000000
    Saving model-1.joblib
    Saving model-2.joblib
    Saving model-3.joblib
    Saving model-4.joblib
    <exit 0>

The dependencies for the train stage include the files from
`prepare-data` and also required source code and configuration. These
are defined in `dvc.yaml` as stage dependency and are so reflected in
the train manifest.

    >>> dvc_config["stages"]["train-models"]["deps"]
    ['iris.npy', 'train_models.py']

    >>> run("guild ls -nd")
    iris.npy
    params.json.in
    train_models.py

`params.json.in` is listed as a dependency because it's specified in
the stage config for `params`.

    >>> dvc_config["stages"]["train-models"]["params"]
    [{'params.json.in': ['train.C', 'train.gamma', 'train.max-iters']}]

Guild captures these parameters as flags.

    >>> run("guild runs info")
    id: ...
    operation: dvc.yaml:train-models
    from: .../dvc.yaml
    status: completed
    ...
    dvc-stage: train-models
    ...
    flags:
      dvcstage:prepare-data: ...
      train.C: 1.0
      train.gamma: 0.7
      train.max-iters: 10000
    scalars:

    >>> run("guild select --attr flags")
    dvcstage:prepare-data: ...
    train.C: 1.0
    train.gamma: 0.7
    train.max-iters: 10000

These are the values defined in `params.json.in`.

    >>> cat("params.json.in")
    {
      "x": 0.1,
      "noise": 0.1,
      "train": {
        "C": 1.0,
        "max-iters": 10000,
        "gamma": 0.7
      },
      "eval": {
        "plot-spacing": 0.4
      }
    }

The train operation generates saved models.

    >>> run("guild ls -ng")
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib

Run the operation using different flag values.

    >>> run("guild run dvc.yaml:train-models train.C=2.0 train.gamma=0.8 -y")
    Resolving dvcfile:train_models.py
    Resolving dvcstage:prepare-data
    Using run ... for dvcstage:prepare-data
    Resolving config:params.json.in
    INFO: [guild] Initializing run
    INFO: [guild] Running stage 'train-models'
    C=2.000000
    gamma=0.800000
    max_iters=10000.000000
    Saving model-1.joblib
    Saving model-2.joblib
    Saving model-3.joblib
    Saving model-4.joblib

    >>> run("guild select --attr flags")
    dvcstage:prepare-data: ...
    train.C: 2.0
    train.gamma: 0.8
    train.max-iters: 10000
