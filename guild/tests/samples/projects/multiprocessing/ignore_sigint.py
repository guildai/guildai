import signal
import time

seconds = 5

def handler(_signum, _stack_frame):
    print("NO")

signal.signal(signal.SIGTERM, handler)
time.sleep(seconds)
