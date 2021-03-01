import os
import time

seconds = 1.0

print("Run %s starting" % (os.getenv("RUN_ID"),))
time.sleep(seconds)
print("Run %s stopping" % (os.getenv("RUN_ID"),))
