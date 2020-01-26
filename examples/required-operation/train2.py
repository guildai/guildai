import os

# Assert that our mock data set is available.

assert os.path.exists("data.txt")

# Simulate a model build by writing some empty file.

open("model.json", "w").close()
open("checkpoint.h5", "w").close()
