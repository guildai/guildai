# Evaluate MNIST intro example

Once an `mnist-intro` model is trained, we can run the `evaluate`
operation to test it against all of the test data.

    >>> cd("examples/mnist")
    >>> run("guild run intro:evaluate -y --no-gpus")
    Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: <none>
    Resolving data dependency...
    Resolving operation:train dependency
    Using output from run ...
    INFO: [tensorflow] Restoring parameters from ./model/export
    Test accuracy=0...
    <exit 0>
