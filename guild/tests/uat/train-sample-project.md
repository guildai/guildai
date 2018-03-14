# Train default project

This test assumes a traininable model exists in `sample-project`:

    >>> run("guild -C sample-project operations")
    Limiting models to 'sample-project' (use --all to include all)
    ./sample-project/sample-project:train  Train the model
    <exit 0>

Here's the prompt for training with default flags:

    >>> run("guild -C sample-project train", timeout=2)
    You are about to run ./sample-project/sample-project:train
      batch-size: 64
      train-steps: 1000
    Continue? (Y/n)
    <exit ...>

Let's train with 5 epochs:

    >>> run("guild -C sample-project train train-steps=100 -y")
    Sample train: step 0
    Sample evaluate: 0.888 accuracy
    <exit 0>
