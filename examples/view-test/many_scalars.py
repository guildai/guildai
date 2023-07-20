import random

tags = [
    "Lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
    "sed", "do", "eiusmod", ",tempor", "incididunt", "ut", "labore", "et", "dolore",
    "magna", "aliqua"
]

for tag in tags:
    print(f"{tag}: {random.random()}")

for tag in tags:
    print(f"{tag}-2: {random.random()}")

for tag in tags:
    print(f"{tag}-3: {random.random()}")
