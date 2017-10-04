import errno
import os
import sys

def find_apply(funs, *args, **kw):
    for f in funs:
        result = f(*args)
        if result is not None:
            return result
    return kw.get("default")

def ensure_dir(d):
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def pid_exists(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def free_port():
    import random
    import socket
    min_port = 49152
    max_port = 65535
    max_attempts = 100
    attempts = 0

    while True:
        if attempts > max_attempts:
            raise RuntimeError("too many free port attempts")
        port = random.randint(min_port, max_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            sock.connect(('localhost', port))
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                return port
        else:
            sock.close()
        attempts += 1

def open_url(url):
    try:
        _open_url_with_cmd(url)
    except OSError:
        _open_url_with_webbrowser(url)

def _open_url_with_cmd(url):
    import subprocess
    if sys.platform == "darwin":
        args = ["open", url]
    else:
        args = ["xdg-open", url]
    with open(os.devnull, "w") as null:
        subprocess.check_call(args, stderr=null, stdout=null)

def _open_url_with_webbrowser(url):
    import webbrowser
    webbrowser.open(url)
