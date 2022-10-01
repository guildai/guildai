import os
import sys

print(f"args: {sys.argv[1:]}")
print(f"env: {os.getenv('FLAG_B')}")
