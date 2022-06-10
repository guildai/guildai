import os

msg = None

if msg:
    print(msg)

# Write some files (used for completions)
open("foo.txt", "w").close()
open("bar.txt", "w").close()
open(f"{msg}.out", "w").close()
open(f".guild/sourcecode/{msg}.src.out", "w").close()

os.mkdir("foo")
open(os.path.join("foo", "xxx.txt"), "w").close()
open(os.path.join("foo", "yyy.txt"), "w").close()
