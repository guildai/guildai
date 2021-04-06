import multiprocessing as mp
import os

import mod

print(os.getpid())

ps = [mp.Process(target=mod.f) for _ in range(3)]
for p in ps:
    p.start()
for p in ps:
    p.join()
