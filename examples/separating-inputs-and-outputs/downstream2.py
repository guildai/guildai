import os
import sys

# Get input and output paths from command args
assert len(sys.argv) == 3, sys.argv
model_in_path, model_out_path = sys.argv[1:]

# Read and verify input model
model_in = open(model_in_path).read()
assert model_in == "upstream", model_in
print("upstream model ok")

# Ensure directory for output model
model_out_dir = os.path.dirname(model_out_path)
if model_out_dir and not os.path.exists(model_out_dir):
    os.makedirs(model_out_dir)

# Write output model
with open(model_out_path, "w") as f:
    f.write("downstream")
