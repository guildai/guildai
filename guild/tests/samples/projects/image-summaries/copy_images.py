import glob
import shutil

for name in glob.glob("*.png"):
    shutil.copy(name, name[:-4] + "-copy.png")
