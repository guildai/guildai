# Train Keras MLP example

Keras models can be trained simply by running them.

    >>> cd(example("keras"))

Lets run the `mnist_mlp.py` script:

    >>> run("guild run mnist_mlp.py -y --no-gpus epochs=1",
    ...     timeout=180, ignore=("WARNING", "Refreshing"))
    Masking available GPUs (CUDA_VISIBLE_DEVICES='')
    Using TensorFlow backend...
    60000/60000 ...
    Test loss: ...
    Test accuracy: ...
    <exit 0>

Here's the run info with all scalars:

    >>> run("guild runs info --all-scalars")
    id: ...
    operation: mnist_mlp.py
    from: .../keras
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: batch_size=128 epochs=1 num_classes=10
    sourcecode_digest: 300881a146e716c461f5f0276daac288
    vcs_commit: git:...
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    flags:
      batch_size: 128
      epochs: 1
      num_classes: 10
    scalars:
      accuracy: ... (step 1)
      loss: ... (step 1)
      test_accuracy: ... (step 1)
      test_loss: ... (step 1)
      val_accuracy: ... (step 1)
      val_loss: ... (step 1)
    <exit 0>

And files (empty list):

    >>> run("guild ls")
    ???:
    <exit 0>
