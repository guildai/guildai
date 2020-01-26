import os

# Fake data to simulate a data prep operation.

open("data1.txt", "w").close()

os.mkdir("subdir")
open("subdir/data2.txt", "w").close()
