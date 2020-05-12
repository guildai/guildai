# Guild Example: `tensorboard`

This example shows various TensorBoard integrations.

- [guild.yml](guild.yml) - Project Guild file
- [mnist.py](mnist.py) - MNIST example

To run the sample [MNIST
trainer](https://www.tensorflow.org/tensorboard/get_started), change
to this directory and run:

    $ guild run mnist:train

Press `Enter` to confirm. Guild runs `mnist.py` according to the
defintiion in [guild.yml](guild.yml). Results are written to a unique
run directory.

When the operation finished, view the generated files:

    $ guild ls

Open the run in TensorBoard:

    $ guild tensorboard 1

The argument `1` indicates that you want to view the latest run in
TensorBoard. This corresponds to the index shown when you list runs:

    $ guild runs

You can view the run directly using TensorBoard. First, get the latest
run directory:

    $ guild runs info

Note the value for `run_dir` in the output and use it in the command:

    $ tensorboard --logdir <run_dir>
