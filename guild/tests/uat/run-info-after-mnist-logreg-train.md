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
    label: epochs=1
    sourcecode_digest: ...
    run_dir: ...
    command: ... guild.op_main logreg --data-dir mnist-idx-data --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    scalars:
      acc: ... (step 550)
      loss: ... (step 550)
      val#acc: ... (step 550)
      val#loss: ... (step 550)
    <exit 0>

We can optionally show env for a run:

    >>> run("guild runs info --env") # doctest: +REPORT_UDIFF
    id: ...
    operation: gpkg.mnist/logreg:train
    from: gpkg.mnist==0.6.0
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: epochs=1
    sourcecode_digest: ...
    run_dir: ...
    command: ... -um guild.op_main logreg --data-dir mnist-idx-data --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    scalars:
      acc: ... (step 550)
      loss: ... (step 550)
      val#acc: ... (step 550)
      val#loss: ... (step 550)
    environment:
      CMD_DIR: ...
      COLUMNS: '999'
      CUDA_VISIBLE_DEVICES: ''
      FLAG_BATCH_SIZE: '100'
      FLAG_EPOCHS: '1'
      FLAG_LEARNING_RATE: '0.5'
      GUILD_HOME: ...
      GUILD_OP: logreg:train
      GUILD_PKG: ...
      GUILD_PKGDIR: ...
      GUILD_PLUGINS: ''
      ...
      LOG_LEVEL: '20'
      ...
      PROJECT_DIR: ...
      ...
      RUN_DIR: ...
      RUN_ID: ...
      ...
    <exit 0>

JSON output:

    >>> tmp = path(mkdtemp(), "info.json")
    >>> quiet("guild runs info --json > %s" % tmp)
    >>> cat_json(tmp)  # doctest: +REPORT_UDIFF
    {
        "command": "... -um guild.op_main logreg --data-dir mnist-idx-data
                    --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5",
        "exit_status": 0,
        "flags": {
            "batch-size": 100,
            "epochs": 1,
            "learning-rate": 0.5
        },
        "from": "gpkg.mnist==0.6.0",
        "id": "...",
        "label": "epochs=1",
        "marked": "no",
        "operation": "gpkg.mnist/logreg:train",
        "pid": "",
        "run_dir": "...",
        "scalars": {
            "acc": [
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
            "val#loss": [
                ...,
                550
            ]
        },
        "sourcecode_digest": "...",
        "started": "...",
        "status": "completed",
        "stopped": "..."
    }

With `--private-attrs`:

    >>> quiet("guild runs info --private-attrs --json > %s" % tmp)
    >>> cat_json(tmp)  # doctest: +REPORT_UDIFF
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
        "label": "epochs=1",
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
                    "GUILD_OP": "logreg:train",
                    "GUILD_PLUGINS": "",
                    "PROJECT_DIR": ".../gpkg/mnist"
                }
            },
            "output-scalars": null,
            "python-requires": null
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
            "loss": [
                ...,
                550
            ],
            "val#acc": [
                ...,
                550
            ],
            "val#loss": [
                ...,
                550
            ]
        },
        "sourcecode_digest": "...",
        "started": "...",
        "status": "completed",
        "stopped": "..."
    }
