import os

# Assert that our required mock data set is available.

assert os.path.exists("data/data1.txt")
assert os.path.exists("data/subdir/data2.txt")

# Simulate a model build by writing some empty file.

open("model.json", "w").close()
open("checkpoint.h5", "w").close()
