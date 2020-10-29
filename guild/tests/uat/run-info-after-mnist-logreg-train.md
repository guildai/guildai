# Run info after `logreg` train

Use `guild runs info` to show information about the latest run:

    >>> run("guild runs info") # doctest: +REPORT_UDIFF
    id: ...
    operation: gpkg.mnist/logreg:train
    from: gpkg.mnist==0.6.0
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: batch-size=100 epochs=1 learning-rate=0.5
    sourcecode_digest: ...
    vcs_commit:
    run_dir: ...
    command: ... -um guild.op_main logreg --data-dir mnist-idx-data --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    tags:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    scalars:
      acc: ... (step 550)
      biases/max_1: ...
      biases/mean_1: ...
      biases/min_1: ...
      biases/stddev: ...
      loss: ... (step 550)
      weights/max_1: ...
      weights/mean_1: ...
      weights/min_1: ...
      weights/stddev: ...
      val#acc: ...
      val#biases/max_1: ...
      val#biases/mean_1: ...
      val#biases/min_1: ...
      val#biases/stddev: ...
      val#loss: ... (step 550)
      val#weights/max_1: ...
      val#weights/mean_1: ...
      val#weights/min_1: ...
      val#weights/stddev: ...
    <exit 0>

We can optionally show env for a run:

    >>> run("guild runs info --env")
    id: ...
    ...
    environment:...
      CMD_DIR: ...
      ...
      CUDA_VISIBLE_DEVICES: ''
      ...
      FLAG_BATCH_SIZE: '100'
      FLAG_EPOCHS: '1'
      FLAG_LEARNING_RATE: '0.5'...
      GUILD_HOME: ...
      GUILD_OP: gpkg.mnist/logreg:train
      GUILD_PKG: ...
      GUILD_PKGDIR: ...
      GUILD_PLUGINS: ''
      GUILD_SOURCECODE: .guild/sourcecode
      ...
      LOG_LEVEL: '20'
      ...
      PROJECT_DIR: .../gpkg/mnist
      ...
      RUN_DIR: ...
      RUN_ID: ...
      ...
    <exit 0>

JSON output, including private attrs:

    >>> tmp = path(mkdtemp(), "info.json")
    >>> quiet("guild runs info --private-attrs --json > %s" % tmp)
    >>> cat_json(tmp)
    {
        "command": "... -um guild.op_main logreg --data-dir mnist-idx-data --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5",
        "exit_status": 0,
        "flags": {
            "batch-size": 100,
            "epochs": 1,
            "learning-rate": 0.5
        },
        "from": "gpkg.mnist==0.6.0",
        "id": "...",
        "label": "batch-size=100 epochs=1 learning-rate=0.5",
        "marked": "no",
        "op": {
            "deps": [
                {
                    "description": "Yann Lecun's MNIST dataset in compressed IDX format",
                    "location": ".../gpkg/mnist",
                    "name": "mnist-dataset",
                    "path": "mnist-idx-data",
                    "private": true,
                    "sources": [
                        {
                            "sha256": "440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
                            "url": "http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz"
                        },
                        {
                            "sha256": "3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
                            "url": "http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz"
                        },
                        {
                            "sha256": "8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
                            "url": "http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz"
                        },
                        {
                            "sha256": "f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6",
                            "url": "http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz"
                        }
                    ]
                }
            ],
            "flag-null-labels": {},
            "flags-extra": {},
            "label-template": null,
            "op-cmd": {
                "cmd-args": [
                    "${python_exe}",
                    "-um",
                    "guild.op_main",
                    "logreg",
                    "--data-dir",
                    "mnist-idx-data",
                    "--run-dir",
                    ".",
                    "--",
                    "__flag_args__"
                ],
                "cmd-env": {
                    "GUILD_PLUGINS": "",
                    "PROJECT_DIR": ".../gpkg/mnist"
                },
                "flags-dest": "args"
            },
            "output-scalars": null,
            "python-requires": null,
            "sourcecode-root": ".guild/sourcecode"
        },
        "operation": "gpkg.mnist/logreg:train",
        "opref": "package:gpkg.mnist 0.6.0 logreg train",
        "pid": "",
        "run_dir": "...",
        "scalars": {
            "acc": [
                ...,
                550
            ],
            "biases/max_1": [
                ...,
                550
            ],
            "biases/mean_1": [
                ...,
                550
            ],
            "biases/min_1": [
                ...,
                550
            ],
            "biases/stddev": [
                ...,
                550
            ],
            "loss": [
                ...,
                550
            ],
            "val#acc": [
                ...,
                550
            ],
            "val#biases/max_1": [
                ...,
                550
            ],
            "val#biases/mean_1": [
                ...,
                550
            ],
            "val#biases/min_1": [
                ...,
                550
            ],
            "val#biases/stddev": [
                ...,
                550
            ],
            "val#loss": [
                ...,
                550
            ],
            "val#weights/max_1": [
                ...,
                550
            ],
            "val#weights/mean_1": [
                ...,
                550
            ],
            "val#weights/min_1": [
                ...,
                550
            ],
            "val#weights/stddev": [
                ...,
                550
            ],
            "weights/max_1": [
                ...,
                550
            ],
            "weights/mean_1": [
                ...,
                550
            ],
            "weights/min_1": [
                ...,
                550
            ],
            "weights/stddev": [
                ...,
                550
            ]
        },
        "sourcecode_digest": "...",
        "started": "...",
        "status": "completed",
        "stopped": "...",
        "tags": [],
        "vcs_commit": ""
    }
