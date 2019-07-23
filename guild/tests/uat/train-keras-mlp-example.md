# Train Keras MLP example

Keras models can be trained simply by running them.

    >>> cd("examples/keras")

Lets run the `mnist_mlp.py` script:

    >>> run("guild run mnist_mlp.py -y --no-gpus epochs=1",
    ...     timeout=180, ignore=("WARNING", "Refreshing"))
    Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: <none>
    Using TensorFlow backend.
    60000 train samples
    10000 test samples...
    _________________________________________________________________
    Layer (type)                 Output Shape              Param #
    =================================================================
    dense_1 (Dense)              (None, 512)               401920
    _________________________________________________________________
    dropout_1 (Dropout)          (None, 512)               0
    _________________________________________________________________
    dense_2 (Dense)              (None, 512)               262656
    _________________________________________________________________
    dropout_2 (Dropout)          (None, 512)               0
    _________________________________________________________________
    dense_3 (Dense)              (None, 10)                5130
    =================================================================
    Total params: 669,706
    Trainable params: 669,706
    Non-trainable params: 0
    _________________________________________________________________
    ...Train on 60000 samples, validate on 10000 samples...
    Epoch 1/1
    <BLANKLINE>
    ...
    test_loss: ...
    test_acc: ...
    <exit 0>

Here's the run info, including files and scalars:

    >>> run("guild runs info --files --scalars")
    id: ...
    operation: mnist_mlp.py
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: epochs=1
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    flags:
      batch_size: 128
      epochs: 1
      num_classes: 10
    scalars:
      acc: ... (step 0)
      loss: ... (step 0)
      sys/...
      val_acc: ... (step 0)
      val_loss: ... (step 0)
      acc: ... (step 1)
      loss: ... (step 1)
      val_acc: ... (step 1)
      val_loss: ... (step 1)
    files:
      events.out.tfevents...
    <exit 0>
