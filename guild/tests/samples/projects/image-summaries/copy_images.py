import os
import shutil

for name in os.listdir("."):
    base, ext = os.path.splitext(name)
    if ext.lower() in (".jpg", ".png"):
        shutil.copy(name, "%s-copy%s" % (base, ext))
