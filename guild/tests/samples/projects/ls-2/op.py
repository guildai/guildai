import os

# Read deps
print(f"dep-1 says: {open('dep-1.txt').read().rstrip()}")
print(f"dep-2 says: {open('dep-2.txt').read().rstrip()}")

# Generate files
print("Generating files")

open("generated-1.txt", "w").close()
open("generated-2.txt", "w").close()

if not os.path.exists("subdir"):
    os.mkdir("subdir")
open("subdir/generated-3.txt", "w").close()

if not os.path.exists(".hidden"):
    os.mkdir(".hidden")
open(".hidden/generated-4.txt", "w").close()
open(".hidden/generated-5.txt", "w").close()
