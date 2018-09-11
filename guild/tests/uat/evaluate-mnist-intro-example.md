# Evaluate MNIST intro example

Once an `mnist-intro` model is trained, we can run the `evaluate`
operation to test it against all of the test data.

    >>> cd("examples/mnist")
    >>> run("guild run intro:evaluate -y --no-gpus")
    Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: <none>
    Resolving model dependency
    Using output from run ... for model resource
    Resolving data dependency
    ...
    Test accuracy=...
    <exit 0>

Markdown finished at Thu Nov 30 19:55:33
