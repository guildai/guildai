import os

# Ensure directory for model.
if not os.path.exists("models"):
    os.mkdir("models")

# Write model.
with open("models/checkpoint.txt", "w") as f:
    f.write("upstream")
