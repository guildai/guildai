import sys
import time

sys.stdout.write("This is to stdout\n")
time.sleep(0.1)
sys.stderr.write("This is to stderr\n")
time.sleep(0.2)
sys.stdout.write("This is delayed by 0.2 seconds\n")
