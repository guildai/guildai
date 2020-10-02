# Train Keras MLP example 2

In this test we run the mnist_mlp example as an operation defined in a
Guild file.

The example is in the `keras` directory.

    >>> cd(example("keras"))

Here are the operations available:

    >>> run("guild ops mlp-mnist")
    mlp-mnist:train  Train MLP on MNIST
    <exit 0>

Train `mlp-mnist`:

    >>> run("guild run mlp-mnist:train -y --no-gpus epochs=1")
    Masking available GPUs (CUDA_VISIBLE_DEVICES='')
    Using TensorFlow backend...
    60000/60000 ...
    Test loss: ...
    Test accuracy: ...
    <exit 0>

Run info:

    >>> run("guild runs info")
    id: ...
    operation: mlp-mnist:train
    from: .../keras/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: batch_size=128 epochs=1
    sourcecode_digest: 106c5dcffffab1f6cbe5e1b50dfac863
    vcs_commit: git:...
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    tags:
    flags:
      batch_size: 128
      epochs: 1
    scalars:
      accuracy: ... (step 1)
      loss: ... (step 1)
      test_accuracy: ... (step 1)
      test_loss: ... (step 1)
      val_accuracy: ... (step 1)
      val_loss: ... (step 1)
    <exit 0>

Files:

    >>> run("guild ls")
    ???:
      weights.01-0...hdf5
    <exit 0>
