try:
    import tensorboardX
except ImportError:
    raise SystemExit(
        "This script uses tensorboardX to log scalars "
        "- install it by running 'pip install "
        "--user tensorboardX'")

# Use summary writer to write scalars with steps.
#
# You can use TensorFlow's summary writer:
#
# https://www.tensorflow.org/api_docs/python/tf/summary/FileWriter
#
# If you're not using TensorFlow, the tensorboardX library (used here)
# is lightweight and works well.
#
# Write the TF event files anywhere in the current working directory
# (the run directory).

writer = tensorboardX.SummaryWriter(".")

# Guild ignores all output from this script when run as `train3` the
# operation because `output-scalars` is disabled (set to `no`) in the
# Guild file (guild.yml).

print("Step 1: loss=2.235 accuracy=0.123")

# Log the scalars for step 1

writer.add_scalar("loss", 2.345, 1)
writer.add_scalar("accuracy", 0.123, 1)

# Log the scalars for step 2

print("Step 2: loss=1.234 accuracy=0.456")
writer.add_scalar("loss", 1.234, 2)
writer.add_scalar("accuracy", 0.456, 2)

writer.close()
