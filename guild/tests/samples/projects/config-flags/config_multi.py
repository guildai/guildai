import os

first = True
for path in sorted(os.listdir()):
    if not os.path.isfile(path):
        continue
    if not first:
        print()
    print(path)
    print("-" * len(path))
    print(open(path).read().strip())
    first = False
