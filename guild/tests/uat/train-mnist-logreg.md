# Train `logreg`

Delete runs in prep for this test.

    >>> quiet("guild runs rm -y")

Train the `logreg` model with one epoch. Note that we don't have to
specify the full model name as long as our term refers to one and only
one model.

    >>> run("guild run -y --no-gpus logreg:train epochs=1")
    Masking available GPUs (CUDA_VISIBLE_DEVICES='')
    Resolving mnist-dataset dependency
    ...
    Step 20:...
    Step 550:...
    ...
    <exit 0>
