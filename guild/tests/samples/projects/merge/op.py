import os

mkdir = os.mkdir


def touch(path):
    open(path, "w").close()


print("Generating files")
touch("a")
touch("b")
mkdir("subdir")
touch("subdir/c")
