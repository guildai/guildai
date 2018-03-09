# Train default project

This test assumes a traininable model exists in `sample-project`:

    >>> run("guild -C sample-project operations")
    Limiting models to 'sample-project' (use --all to include all)
    ./sample-project/sample-project:train  Train the model
    <exit 0>

Here's the prompt for training with default flags:

    >>> run("guild -C sample-project train", timeout=1)
    You are about to run ./sample-project/sample-project:train
      batch-size: 64
      epochs: 20
      learning-rate: 0.01
    Continue? (Y/n)
    <exit ...>

Let's train with 5 epochs:

    >>> run("guild -C sample-project train epochs=5 -y")
    Resolving data dependency...
    Training sample model (batch-size: 64, learning-rate: 0.01): epoch 1
    Training sample model (batch-size: 64, learning-rate: 0.01): epoch 2
    Training sample model (batch-size: 64, learning-rate: 0.01): epoch 3
    Training sample model (batch-size: 64, learning-rate: 0.01): epoch 4
    Training sample model (batch-size: 64, learning-rate: 0.01): epoch 5
    <exit 0>
