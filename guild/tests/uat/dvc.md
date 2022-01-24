# DvC support

These tests cover DvC support. The 'dvc' example contains the related
source we test.

    >>> cd(example("dvc"))

Ensure that DvC reqs are installed.

    >>> quiet("python -m pip install -r requirements.txt")

## Project operations

Refer to the Guild file for the example for details.

    >>> run("guild ops")
    hello                 Stage 'hello' imported from dvc.yaml
    hello-dvc-pipeline    DvC hello pipeline
    hello-dvc-stage       DvC hello stage
    hello-guild-op        Guild hello operation
    hello-guild-pipeline  Sample Guild pipeline (contrast to DvC hello pipeline)
    all-dvc:eval-models   Stage 'eval-models' imported from dvc.yaml
    all-dvc:hello         Stage 'hello' imported from dvc.yaml
    all-dvc:prepare-data  Stage 'prepare-data' imported from dvc.yaml
    all-dvc:train-models  Stage 'train-models' imported from dvc.yaml
    iris:eval-models      Evaluate trained Iris models
    iris:prepare-data     Prepare Iris data for model training
    iris:train-models     Train Iris models
    <exit 0>

## Importing DvC stages

Guild supports import of stages defined in dvc.yaml.

    >>> cat("guild.yml")
    - model: ''
      extra:
        dvc-stages-import: hello
    ...
    - model: iris
      extra:
        dvc-stages-import:
          - prepare-data
          - train-models
          - eval-models
    ...
    - model: all-dvc
      extra:
        dvc-stages-import: all

## Using 'dvc pull' in pre-processing

To run `dvc pull` prior to resolving a project file, a resource source
can use the `pre-process` attribute. In our example, the
'hello-guild-op' operation relies on `hello.in`. It uses `pre-process`
to ensure that the DvC managed file `hello.in` is available locally
before resolving it.

    >>> cat("guild.yml")
    ???
        hello-guild-op:
          main: hello
          description: Guild hello operation
          requires:
            - file: hello.in
              pre-process: dvc pull hello.in
    ...

To illustrate, delete the required file.

    >>> rm("hello.in", force=True)

When we run 'hello-guild-op' DvC is used to restore the file.

    >>> run("guild run hello-guild-op -y")
    Resolving file:hello.in dependency
    Pre processing file:hello.in resource in .../examples/dvc: 'dvc pull hello.in'
    A       hello.in
    1 file added
    <exit 0>

    >>> run("guild ls -n")
    hello.in
    hello.out
    <exit 0>

    >>> run("guild cat -p hello.in")
    Guild
    <exit 0>

    >>> run("guild cat -p hello.out")
    Hello! Guild
    <exit 0>

## Run stages defined in dvc.yaml

Guild can run stages defined in dvc.yaml using the special operation
name syntax `dvc.yaml:<stage>`.

    >>> run("guild run dvc.yaml:hello --help-op")
    Usage: guild run [OPTIONS] dvc.yaml:hello [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      copy-deps   Whether or not to copy stage dependencies to the run directory.
                  Note that '*.dvc' files are always copied when available.
                  (default is no)
    <BLANKLINE>
      pipeline    Run stage as pipeline. This runs stage dependencies first.
                  (default is no)
    <BLANKLINE>
      pull-first  Run 'dvc pull' before running stages. (default is no)
    <exit 0>

Verify that `hello.in` exists before running the stage.

    >>> exists("hello.in")
    True

Run the stage.

    >>> run("guild run dvc.yaml:hello -y")
    INFO: [guild] Running DvC stage hello
    'hello.in.dvc' didn't change, skipping
    Stage 'hello' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying hello.out
    <exit 0>

By default, Guild copies the DvC metadata files and the stage outputs
but not deps.

    >>> run("guild ls -n")
    dvc.lock
    dvc.yaml
    hello.out
    <exit 0>

    >>> run("guild cat -p hello.out")
    Hello! Guild
    <exit 0>

Dependencies can be copied by setting the `copy-deps` flag to `yes`.

    >>> run("guild run dvc.yaml:hello copy-deps=yes -y")
    INFO: [guild] Running DvC stage hello
    'hello.in.dvc' didn't change, skipping
    Stage 'hello' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying hello.in
    INFO: [guild] Copying hello.py
    INFO: [guild] Copying hello.out
    <exit 0>

    >>> run("guild ls -n")
    dvc.lock
    dvc.yaml
    hello.in
    hello.out
    hello.py
    <exit 0>

    >>> run("guild cat -p hello.in")
    Guild
    <exit 0>

    >>> run("guild cat -p hello.out")
    Hello! Guild
    <exit 0>

By default, Guild does not run 'dvc pull' before running a stage. You
can run 'dvc pull' by setting the `pull-first` flag to `yes`.

Delete 'hello.in' first.

    >>> rm("hello.in")

Run the stage, pulling first.

    >>> run("guild run dvc.yaml:hello pull-first=yes -y")
    INFO: [guild] Running DvC stage hello
    INFO: [guild] Pulling DvC files
    ...
    'hello.in.dvc' didn't change, skipping
    Stage 'hello' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying hello.out
    <exit 0>

## Run imported stage

Stages are imported from dvc.yaml using `dvc-stages-import` extra attr
for a model (see above).

    >>> run("guild run hello --help-op")
    Usage: guild run [OPTIONS] hello [FLAG]...
    <BLANKLINE>
    Stage 'hello' imported from dvc.yaml
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      copy-deps   Whether or not to copy stage dependencies to the run directory.
                  Note that '*.dvc' files are always copied when available.
                  (default is no)
    <BLANKLINE>
      pipeline    Run stage as pipeline. This runs stage dependencies first.
                  (default is yes)
    <BLANKLINE>
      pull-first  Run 'dvc pull' before running stages. (default is yes)
    <exit 0>

Note in the case of importing a stage:

- Stage is imported as a pipeline
- pull-first defaults to yes

Run the imported stage.

    >>> run("guild run hello -y")
    INFO: [guild] Pulling DvC files
    Everything is up to date.
    INFO: [guild] Running DvC stage hello
    'hello.in.dvc' didn't change, skipping
    Stage 'hello' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying hello.out
    <exit 0>

When run as a pipeline, a stage acts like a steps parent.

    >>> run("guild runs -n2")
    [1:...]  dvc.yaml:hello  ...  completed  copy-deps=no pipeline=no pull-first=no
    [2:...]  hello           ...  completed  copy-deps=no pipeline=yes pull-first=yes
    <exit 0>

Each stage is linked from the parent.

    >>> run("guild ls 2 -L -n")
    hello/
    hello/.guild/
    ...
    hello/dvc.lock
    hello/dvc.yaml
    hello/hello.out
    <exit 0>

## Run a complex pipeline

The 'iris:eval-models' pipeline is a full model training and
evaluation scenario. When run, the stage causes 'iris:prepare-data'
and 'iris:train-models' to run as dependencies.

To show the full pipeline, we first delete all DvC managed and
generated files.

    >>> rm("iris.csv", force=True)
    >>> rm("iris.npy", force=True)
    >>> rm("model-1.joblib", force=True)
    >>> rm("model-2.joblib", force=True)
    >>> rm("model-3.joblib", force=True)
    >>> rm("model-4.joblib", force=True)
    >>> rm("models-eval.png", force=True)
    >>> rm("models-eval.json", force=True)

Run the imported pipeline.

    >>> run("guild run iris:eval-models -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Pulling DvC files
    ...
    INFO: [guild] Running DvC stage prepare-data
    'iris.csv.dvc' didn't change, skipping
    Stage 'prepare-data' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying iris.npy
    INFO: [guild] Running DvC stage train-models
    'iris.csv.dvc' didn't change, skipping
    Stage 'prepare-data' didn't change, skipping
    Stage 'train-models' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying model-1.joblib
    INFO: [guild] Copying model-2.joblib
    INFO: [guild] Copying model-3.joblib
    INFO: [guild] Copying model-4.joblib
    INFO: [guild] Running DvC stage eval-models
    'iris.csv.dvc' didn't change, skipping
    Stage 'prepare-data' didn't change, skipping
    Stage 'train-models' didn't change, skipping
    Stage 'eval-models' is cached - skipping run, checking out outputs
    Use `dvc push` to send your updates to remote storage.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying models-eval.png
    INFO: [guild] Copying models-eval.json
    <exit 0>

The pipeline runs with three stages.

    >>> run("guild runs -n4")
    [1:...]  dvc.yaml:eval-models   ...  completed  copy-deps=no pipeline=no pull-first=no
    [2:...]  dvc.yaml:train-models  ...  completed  copy-deps=no pipeline=no pull-first=no
    [3:...]  dvc.yaml:prepare-data  ...  completed  copy-deps=no pipeline=no pull-first=no
    [4:...]  iris:eval-models       ...  completed  copy-deps=no pipeline=yes pull-first=yes
    <exit 0>

    >>> run("guild ls 4 -n")
    eval-models/
    prepare-data/
    train-models/
    <exit 0>

Each stage contains outputs and DvC metadata files.

`iris:prepare-data`:

    >>> run("guild ls 3 -n")
    dvc.lock
    dvc.yaml
    iris.npy
    <exit 0>

`iris:train-models`:

    >>> run("guild ls 2 -n")
    dvc.lock
    dvc.yaml
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    <exit 0>

`iris:eval-models`:

    >>> run("guild ls 1 -n")
    dvc.lock
    dvc.yaml
    events.out.tfevents...
    models-eval.json
    models-eval.png
    <exit 0>

Note that 'iris:eval-models' also contains a TF events file. In this
case, Guild converts metrics written to 'models-eval.json' to
scalars. We can view these as run info.

    >>> run("guild runs info")
    id: ...
    operation: dvc.yaml:eval-models
    from: guildai
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: copy-deps=no pipeline=no pull-first=no
    sourcecode_digest:
    vcs_commit:
    run_dir: ...
    command: ... -um guild.plugins.dvc_stage_main --project-dir .../examples/dvc eval-models
    exit_status: 0
    pid:
    tags:
    flags:
      copy-deps: no
      pipeline: no
      pull-first: no
    scalars:
      modle-1-score: 0... (step 0)
      modle-2-score: 0... (step 0)
      modle-3-score: 0... (step 0)
      modle-4-score: 0... (step 0)
    <exit 0>

We can tell Guild to also copy dependencies for each run by setting
`copy-deps` to `yes` for the pipeline. We'll also tell Guild not to
run dvc pull.

    >>> run("guild run iris:eval-models "
    ...     "copy-deps=yes pull-first=no -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] Running DvC stage prepare-data
    'iris.csv.dvc' didn't change, skipping
    Stage 'prepare-data' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying iris.csv
    INFO: [guild] Copying prepare_data.py
    INFO: [guild] Copying iris.npy
    INFO: [guild] Running DvC stage train-models
    'iris.csv.dvc' didn't change, skipping
    Stage 'prepare-data' didn't change, skipping
    Stage 'train-models' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying iris.npy
    INFO: [guild] Copying train_models.py
    INFO: [guild] Copying model-1.joblib
    INFO: [guild] Copying model-2.joblib
    INFO: [guild] Copying model-3.joblib
    INFO: [guild] Copying model-4.joblib
    INFO: [guild] Running DvC stage eval-models
    'iris.csv.dvc' didn't change, skipping
    Stage 'prepare-data' didn't change, skipping
    Stage 'train-models' didn't change, skipping
    Stage 'eval-models' didn't change, skipping
    Data and pipelines are up to date.
    INFO: [guild] Copying dvc.yaml
    INFO: [guild] Copying dvc.lock
    INFO: [guild] Copying model-1.joblib
    INFO: [guild] Copying model-2.joblib
    INFO: [guild] Copying model-3.joblib
    INFO: [guild] Copying model-4.joblib
    INFO: [guild] Copying eval_models.py
    INFO: [guild] Copying models-eval.png
    INFO: [guild] Copying models-eval.json
    <exit 0>

    >>> run("guild runs -n4")
    [1:...]  dvc.yaml:eval-models   ...  completed  copy-deps=yes pipeline=no pull-first=no
    [2:...]  dvc.yaml:train-models  ...  completed  copy-deps=yes pipeline=no pull-first=no
    [3:...]  dvc.yaml:prepare-data  ...  completed  copy-deps=yes pipeline=no pull-first=no
    [4:...]  iris:eval-models       ...  completed  copy-deps=yes pipeline=yes pull-first=no
    <exit 0>

And the files for each run.

    >>> run("guild ls 4 -n")
    eval-models/
    prepare-data/
    train-models/
    <exit 0>

    >>> run("guild ls 3 -n")
    dvc.lock
    dvc.yaml
    iris.csv
    iris.npy
    prepare_data.py
    <exit 0>

    >>> run("guild ls 2 -n")
    dvc.lock
    dvc.yaml
    iris.npy
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    train_models.py
    <exit 0>

    >>> run("guild ls 1 -n")
    dvc.lock
    dvc.yaml
    eval_models.py
    events.out.tfevents...
    model-1.joblib
    model-2.joblib
    model-3.joblib
    model-4.joblib
    models-eval.json
    models-eval.png
    <exit 0>


## Use `guild.plugins.dvc_stage_main` in a custom operation
