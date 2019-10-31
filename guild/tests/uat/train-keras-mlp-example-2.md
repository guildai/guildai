# Train Keras MLP example 2

In this test we run the mnist_mlp example as an operation defined in a
Guild file.

The example is in the `keras` directory.

    >>> cd("examples/keras")

Here are the operations available:

    >>> run("guild ops mlp-mnist", ignore="Refreshing")
    mlp-mnist:train  Train MLP on MNIST
    <exit 0>

Train `mlp-mnist`:

    >>> run("guild run mlp-mnist:train -y --no-gpus epochs=1")
    Masking available GPUs (CUDA_VISIBLE_DEVICES='')
    Using TensorFlow backend...
    60000/60000 ...
    test_loss: ...
    test_acc: ...
    <exit 0>

Run info:

    >>> run("guild runs info --all-scalars")
    id: ...
    operation: mlp-mnist:train
    from: .../keras/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: epochs=1
    sourcecode_digest: 7bfd666a0adc81544179c315d69426ca
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    flags:
      batch_size: 128
      epochs: 1
    scalars:
      accuracy: ... (step 0)
      loss: ... (step 0)
      test_acc: ... (step 0)
      test_loss: ... (step 0)
      val_accuracy: ... (step 0)
      val_loss: ... (step 0)
    <exit 0>

Files:

    >>> run("guild ls")
    ???:
      events.out.tfevents...
    <exit 0>
